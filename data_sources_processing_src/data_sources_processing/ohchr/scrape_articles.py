import argparse
import io
import logging
import os
import re
from itertools import groupby
from typing import List

import docx
import fitz
import pandas as pd
import pytesseract
import requests
from bs4 import BeautifulSoup
from nltk.tokenize import sent_tokenize, word_tokenize
from PIL import Image
from tqdm import tqdm

tqdm.pandas()

logging.basicConfig(
    level=logging.DEBUG,  # Set the logging level
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",  # Log message format
)
logger = logging.getLogger(__name__)

ohchr_data_path = os.path.join("/data", "datasources", "ohchr")


def _map_countries(input_country: str) -> str:
    countries_mapping = {
        # "Central African Republic": "CAR",
        "Democratic People's Republic of Korea": "DPRK",
        "Democratic Republic of the Congo": "Congo DRC",
        "Iran (Islamic Republic of)": "Iran",
        # "Lao People's Democratic Republic": "Laos",
        # "Republic of Moldova": "Moldova",
        "State of Palestine": "Palestine",
        # "Russian Federation": "Russia",
        "Syrian Arab Republic": "Syria",
        # "United Republic of Tanzania": "Tanzania",
        # "Timor-Leste": "Timor Leste",
        "Venezuela (Bolivarian Republic of)": "Venezuela",
    }
    if input_country in countries_mapping:
        return countries_mapping[input_country]
    return input_country


def _sentence_contains_repeated_characters(string, n_repeated=5):
    for char, group in groupby(string):
        if len(list(group)) > n_repeated:
            return True

    return False


def _sentence_is_valid(s: str):
    if (
        len(word_tokenize(s)) < 5
        or len(word_tokenize(s)) > 90
        or len(s) < 10
        or _sentence_contains_repeated_characters(s)
        or "http" in s.lower()
        or "www" in s.lower()
    ):
        return False
    return True


def _remove_return_to_lines_extra_spaces(input_string):
    return re.sub(r"\s+", " ", input_string)


def _get_all_extracted_text(text: List[str]) -> str:
    paragraphs = [_remove_return_to_lines_extra_spaces(s) for s in text]
    valid_sentences = " ".join(
        [" ".join([s for s in sent_tokenize(one_paragraph) if _sentence_is_valid(s)]) for one_paragraph in paragraphs]
    )
    return valid_sentences


def get_text_from_link(row: pd.Series, data_file_path: os.PathLike) -> str:
    """
    Inputs:
        - row (pd.Series): A row from a DataFrame containing document metadata.
        - data_file_path (os.PathLike): Path to the directory where documents are stored.

    Outputs:
        - str: Extracted text from the document.

    Operations:
        1. Construct the file path for the document based on metadata.
        2. Download the document if it does not exist locally.
        3. Extract text from the document based on its type (DOCX or PDF).
        4. Apply OCR for handwritten PDFs if the initial extraction is empty.
        5. Combine all extracted text.
        6. Handle any errors and provide information about the failure.
    """
    doc_type = row["doc_type"]
    file_path = os.path.join(data_file_path, f"{row['Symbol/Title'].replace('/', '-')}.{doc_type}")

    try:
        if not os.path.exists(file_path):
            _download_document(
                row["doc_link"],
                file_path,
            )
        if doc_type == "docx":
            extracted_text = _extract_docx_text(file_path)
        elif doc_type == "pdf":
            extracted_text = _extract_pdf_text(file_path)

        if len(extracted_text) == 0:
            extracted_text = _ocr_handwritten_pdf(file_path)
    except Exception as e:
        logger.error(f"failed to process row. {str(e)}")
        logger.error(f"Download Link {row['Download Link']}")
        logger.error(f"doc_link {row['doc_link']}")
        logger.error(f"Symbol/Title {row['Symbol/Title']}")

        extracted_text = []

    extracted_text = _get_all_extracted_text(extracted_text)

    return extracted_text


def html_doc2df(html_file_path: os.PathLike = os.path.join("all_crc_reports.html")):
    """
    Reads an HTML file from the specified path, defaulting to 'all_crc_reports.html' in the "data" directory.
    The file "all_crc_reports.html" is downloaded manually from the OHCHR website.
    Parses the HTML to extract the contents of the first table it finds, skipping the table's header row.
    Iterates through the table rows, extracting text from each cell and replacing the text
    of the last column with a hyperlink URL if present.
    Compiles the extracted data into a list, with each list item representing a row in the table.
    Constructs a pandas DataFrame from the list, assigning predefined column names that reflect the table's structure.
    Returns the DataFrame, providing a structured and manipulable representation of the
    table data for further analysis or processing.
    """

    # read html file
    with open(html_file_path) as html_file:
        soup = BeautifulSoup(html_file, "html.parser")

    # Find the table
    table = soup.find("table")

    # Extract rows from the table
    rows = table.find_all("tr")[1:]  # Skipping the header row

    # Extracting the data
    data = []
    for i, row in enumerate(rows):
        cols = row.find_all("td")
        cols = [ele.text.strip() for ele in cols]
        # For the last column (Download), extract the URL instead of text
        if row.find("a"):
            cols[-1] = row.find("a").get("href")
            data.append(cols)

    # Define column names based on the table structure
    column_names = [
        "Title",
        "Document Type",
        "Treaty",
        "Country",
        "Symbol/Title",
        "Submitted Date",
        "Download Link",
    ]

    # Create a pandas DataFrame
    df = pd.DataFrame(data, columns=column_names)
    return df


def _get_link(child_link: str):
    """
    This function constructs a URL by appending a given child_link to a predefined original_parent_link.
    It makes a GET request to the constructed URL to fetch the HTML content.
    It parses the HTML to find a hyperlink (<a> tag) with an ID containing "Docx".
    If found, it extracts the href attribute as the document link.
    If the href doesn't start with "http", it adjusts the link to be a full URL.
    If no "Docx" link is found, it looks for a PDF link instead and updates the doc_type.
    Returns the fully qualified document link and the document type ("docx" or "pdf").
    """
    original_parent_link = "https://tbinternet.ohchr.org"
    url = original_parent_link + child_link

    # Send a GET request
    response = requests.get(url)
    doc_type = "docx"

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")
    link_tag = soup.find("a", id=lambda id: id and "Docx" in id)
    link = link_tag.get("href") if link_tag else None

    if link and not link.startswith("http"):
        if link.startswith("/"):
            link = original_parent_link + link
        else:
            link = soup.find("a", id=lambda id: id and "pdf" in id.lower())
            if link:
                link = link.get("href")
                doc_type = "pdf"
                if link.startswith("/"):
                    link = original_parent_link + link
    return link, doc_type


def _download_document(doc_url: str, doc_title: str):
    """
    Sends a GET request to the URL of a document.
    If the request is successful (status code 200), it writes the content of the response
    to a file named doc_title in binary write mode, effectively downloading the document.
    If the URL is "NOT FOUND" or the request fails, it either does nothing or prints an error message, respectively.
    """

    if doc_url == "NOT FOUND":
        return

    response = requests.get(doc_url)

    # Check if the request was successful
    if response.status_code == 200:
        # Open a file in binary write mode
        with open(doc_title, "wb") as file:
            file.write(response.content)
    else:
        logger.error(f"Failed to retrieve the {doc_url} file")


def _extract_docx_text(file_path) -> List[str]:
    """
    Loads a DOCX document from a given file path.
    Iterates through the paragraphs of the document, extracting and concatenating the text from each paragraph into a list.
    Returns the list of all text blocks found in the document.
    """
    # Load the document
    doc = docx.Document(file_path)

    # Extract and concatenate all the text
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)

    return full_text


def _extract_pdf_text(file_path: str) -> List[str]:
    """
    Opens a PDF file from a given file path using fitz (PyMuPDF).
    Iterates through each page of the PDF, extracting text blocks.
    Each block, presumed to represent a paragraph or text element, is added to a list if it contains non-empty text.
    Closes the PDF document and returns the list of text paragraphs.
    """
    # Open the PDF file
    doc = fitz.open(file_path)

    paragraphs = []
    for page in doc:
        blocks = page.get_text("blocks")
        # Each block represents a paragraph or text element
        for block in blocks:
            text = block[4].strip()  # The text of the block
            if text:  # Only add non-empty paragraphs
                paragraphs.append(text)

    doc.close()
    return paragraphs


def _ocr_handwritten_pdf(file_path) -> List[str]:
    """
    Opens a PDF file and initializes an empty list to hold the OCR-extracted text.
    Iterates through each page of the PDF, rendering it to an image.
    Uses Tesseract OCR, via pytesseract.image_to_string, to extract text from the image of each page.
    Appends the extracted text to the list and closes the PDF document after processing all pages.
    Returns the list of extracted text blocks.
    """
    # Open the PDF
    doc = fitz.open(file_path)
    text = []

    for page_num in tqdm(range(len(doc)), desc="OCR Extracting text from PDF"):
        # Get the page
        page = doc.load_page(page_num)

        # Render page to an image
        pix = page.get_pixmap()
        image_bytes = pix.tobytes("png")
        image = Image.open(io.BytesIO(image_bytes))

        # Use Tesseract to do OCR on the image
        text.append(pytesseract.image_to_string(image))

    doc.close()
    return text


def _preprocess_title(row: pd.Series) -> str:
    title = row["Title"].strip()
    symbol_title = row["Symbol/Title"].strip()
    if title == symbol_title:
        final_title = title
    else:
        final_title = f"{title} - {symbol_title}"
    final_title = final_title.replace("/", "-")
    return final_title


def main(use_sample: bool):
    """
    Inputs:
        - use_sample (bool): Whether to use a sample of the data or the full dataset.

    Outputs:
        - None (Saves a CSV file with sorted document data.)

    Operations:
        1. Load and preprocess data from HTML and CSV files.
        2. Map country names and preprocess document titles.
        3. Filter the data based on country list and optionally sample a subset.
        4. Generate document links and types.
        5. Extract text from document links and calculate word counts.
        6. Filter out documents with fewer than 10 words.
        7. Aggregate word counts by country and sort documents accordingly.
        8. Save the processed and sorted data to a CSV file.
    """

    df = html_doc2df()
    countries = pd.read_csv(os.path.join(ohchr_data_path, "..", "..", "report_countries.csv"), header=None)[0].tolist()
    df["Country"] = df["Country"].apply(_map_countries)
    df["Title"] = df.apply(_preprocess_title, axis=1)
    df = df[df.Country.isin(countries)]
    if use_sample:
        df = df.sample(30)

    # if not use_sample:
    #     not_processed_countries = [c for c in countries if c not in df.Country.unique()]
    #     assert (
    #         len(not_processed_countries) == 0
    #     ), f"Following countries are not processed: {not_processed_countries}"

    df["doc_link"] = df["Download Link"].progress_apply(_get_link)
    df["doc_type"] = df["doc_link"].apply(lambda x: x[1])
    df["doc_link"] = df["doc_link"].apply(lambda x: x[0])

    data_file_path = os.path.join(ohchr_data_path, "input_data", "downloaded_documents")
    os.makedirs(data_file_path, exist_ok=True)

    df["extracted_text"] = df.progress_apply(lambda row: get_text_from_link(row, data_file_path), axis=1)
    df["n_words"] = df["extracted_text"].apply(lambda x: len(word_tokenize(x)))
    df = df[df.n_words > 10]

    all_docs_name = "all-docs.csv" if not use_sample else "all-docs-sample.csv"

    grouped_docs = df.groupby("Country", as_index=False).agg({"n_words": "sum"})
    # sort all_docs by n_words
    all_docs_sorted = df.merge(grouped_docs, on="Country", suffixes=("", "_country")).sort_values(
        ["n_words_country", "Country"], ascending=[True, True]
    )

    all_docs_sorted.to_csv(os.path.join(ohchr_data_path, "input_data", all_docs_name), index=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--use_sample", type=str, default="false")
    args = parser.parse_args()
    use_sample = args.use_sample == "true"

    main(use_sample)
