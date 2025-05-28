from typing import List

import numpy as np
import torch
import torch.nn.functional as F
from torch import Tensor, float16
from tqdm import tqdm
from transformers import AutoModel, AutoTokenizer


class EmbeddingsGenerator:
    def __init__(self, model_name: str = "thenlper/gte-small"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModel.from_pretrained(model_name)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        self.embedding_size = self.model.config.hidden_size

    def _average_pool(
        self, last_hidden_states: Tensor, attention_mask: Tensor
    ) -> Tensor:
        last_hidden = last_hidden_states.masked_fill(
            ~attention_mask[..., None].bool(), 0.0
        )
        embeddings = last_hidden.sum(dim=1) / attention_mask.sum(dim=1)[
            ..., None
        ].clamp(min=1e-9)
        normalized_embeddings = F.normalize(embeddings, p=2, dim=-1)
        normalized_embeddings_float16 = normalized_embeddings.to(dtype=float16)
        return normalized_embeddings_float16

    def _generate_embeddings_batch(self, batch_texts: List[str]) -> Tensor:
        batch_dict = self.tokenizer(
            batch_texts,
            padding="longest",
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        batch_dict = {k: v.to(self.device) for k, v in batch_dict.items()}
        outputs = self.model(**batch_dict)
        embeddings = self._average_pool(
            outputs.last_hidden_state, batch_dict["attention_mask"]
        )
        return embeddings

    def __call__(self, input_texts: List[str], batch_size: int = 64) -> Tensor:
        """
        Inputs:
            - input_texts (List[str]): List of input text sentences.
            - batch_size (int): Size of the batches for processing.

        Outputs:
            - Tensor: Tensor containing embeddings for the input texts.

        Operations:
            1. Calculate the number of input texts.
            2. Convert input texts to a NumPy array.
            3. Compute sentence lengths and sort indices based on these lengths.
            4. Sort sentences according to the sorted indices.
            5. Create an empty tensor for embeddings.
            6. Generate embeddings for sentences in batches or all at once.
            7. Place the embeddings in the correct order based on original indices.
            8. Return the final tensor of embeddings.
        """
        n_input_texts = len(input_texts)
        input_sentences = np.array(input_texts)
        sentences_lengths = np.array(
            [len(sentence.split()) for sentence in input_texts]
        )
        sorted_indices = np.argsort(sentences_lengths)
        sorted_sentences = input_sentences[sorted_indices].tolist()

        sorted_inputs_embeddings = torch.zeros(
            (n_input_texts, self.embedding_size), dtype=float16
        )
        with torch.inference_mode():

            if n_input_texts < batch_size:
                sorted_inputs_embeddings = self._generate_embeddings_batch(
                    sorted_sentences
                ).cpu()
            else:
                for i in tqdm(
                    range(0, n_input_texts, batch_size), desc="Generating embeddings"
                ):
                    sorted_batch = sorted_sentences[i: i + batch_size]
                    embeddings_batch = self._generate_embeddings_batch(
                        sorted_batch
                    ).cpu()
                    sorted_inputs_embeddings[i: i + batch_size] = embeddings_batch

        final_embeddings = torch.zeros_like(sorted_inputs_embeddings, dtype=float16)
        final_embeddings[sorted_indices] = sorted_inputs_embeddings

        return final_embeddings


def _generate_embeddings(loaded_df, embeddings_generator):
    input_text = [
        f"passage: {' '.join(sentence)}"
        for sentence in loaded_df["Sentences Groups"].tolist()
    ]
    dataset_embeddings = embeddings_generator(input_text)
    dataset_embeddings = [row.tolist() for row in dataset_embeddings.cpu()]
    loaded_df["Embeddings"] = dataset_embeddings

    return loaded_df
