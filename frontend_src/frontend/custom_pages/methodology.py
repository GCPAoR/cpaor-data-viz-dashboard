import streamlit as st

from frontend.src.utils.utils_functions import _custom_title


def _show_methodological_details():
    # Add the main content
    st.markdown(
        """
    This product showcases a comprehensive collection of data sources and indicators pertinent to child protection
    (using the Needs Identification Analysis Framework (NIAF) as a basis), streamlined through a central online platform.
    Utilizing open-source technologies, the application enhances the coordination and management of humanitarian data,
    facilitating rapid access to vital information and analytics for child protection efforts globally.
    """
    )

    # Section: Technology and Tools
    _custom_title("Technology and Tools", 24)
    st.markdown(
        """
    **Python:** The backbone of our data processing, Python provides the flexibility and robust capabilities required
    for advanced data manipulation and analysis. Its extensive libraries support a variety of functionalities from
    data scraping to deep learning, making it ideal for backend development.

    **Streamlit:** This open-source framework allows for the quick creation of interactive and user-friendly web application.
    Streamlit interfaces seamlessly with Python, enabling real-time data updates and interactive visualization, which
    are crucial for dynamic data displays and user engagement.
    """
    )

    # Section: Application Features
    _custom_title("Application Features", 24)
    st.markdown(
        """
    **Interactive Dashboards:** Users can interact with a variety of data visualizations, including risk maps, country
    profiles, and child protection summaries. These dashboards dynamically adapt to new data, providing up-to-date insights.

    **Automated Data Integration:** Leveraging APIs from key humanitarian organizations, the platform automates the data
    collection and integration process, ensuring a consistent and reliable data flow.

    **Natural Language Processing (NLP):** Utilizing NLP techniques, the application processes vast amounts of unstructured
    data from diverse reports and documents. This feature automatically tags, summarizes, and extracts crucial information,
    transforming verbose documents into concise, actionable insights.

    **Machine Learning Analysis:** The application employs machine learning algorithms to analyze trends and patterns within
    the data, supporting decision-making processes.

    **Customizable Indicators and Filters:** Users can select specific indicators and filters to view customized data sets
    that meet their unique requirements, enhancing the app’s utility.
    """
    )

    # Section: Security and Accessibility
    _custom_title("Security and Accessibility", 24)
    st.markdown(
        """
    The application is designed with a focus on security. Sensitive data might be protected through access control measures.
    It is accessible across multiple devices, providing a consistent user experience that facilitates global access by child
    protection actors and other stakeholders.
    """
    )

    # Section: Data Sources
    _custom_title("Update Frequency of Data Sources", 24)

    # ruff: noqa: E501
    st.markdown(
        """
    This product is updated every 10 days, and scripts are run to update each data source at different intervals, depending
    on the source's data update schedule. Please refer to the specific methodology of each data source to understand their
    individual update frequencies:

    The data displayed in this application is sourced from various respected organizations, including ACLED, ACAPS, UNICEF,
    IPC, OHCHR, and IDMC. Each source has its own methodology, which can be accessed through the following links to ensure
    the accurate interpretation and use of the data:
    - **[ACLED Methodology](https://www.acleddata.com/wp-content/uploads/2017/12/Methodology-Overview_FINAL.pdf)**: Update
    every 7 days.
    - **[ACAPS Protection Indicators](https://www.acaps.org/fileadmin/Dataset/Codebook/20230227_acaps_dataset_protection_indicators_codebook.pdf)**: Update every 7 days.
    - **[ACAPS INFORM Severity Index](https://www.acaps.org/fileadmin/Dataset/Methodology_files/20201019_inform_severity_index_methodology_update.pdf)** Update every 10 days.
    - **[Humanitarian Reference Maps](http://fieldmaps.io/)**: Update every 360 days.
    - **[IPC Scales](https://www.ipcinfo.org/fileadmin/user_upload/ipcinfo/docs/communication_tools/brochures/IPC_Brochure_Understanding_the_IPC_Scales.pdf)**: Update every 60 days.
    - **[IDMC Monitoring Tools](https://www.internal-displacement.org/monitoring-tools/)**: Update every 360 days.
    - **[OCHA HPC Humanitarian Programme Cycle](https://github.com/UN-OCHA/hpc-api/wiki)**: Update every 90 days.
    - **[OHCHR, UN treaty body Database, Committee on the rights of the Child](https://www.ohchr.org/en/resources/databases)**: Update every 360 days
    - **[UNICEF Indicators](https://data.unicef.org/wp-content/uploads/2018/03/Progress-for-Every-Child-ANNEXES-03.06.2018.pdf), [Methodological Work](https://mics.unicef.org/methodological-work), [Indicator Manual](https://www.unicef.org/media/55526/file/UNICEF%20Strategic%20Plan%20Goal%20Area%203%20Indicator%20Manual%20Ver.%201.7.pdf)**: Update every 360 days.

    Global Child Protection Area of Responsibility (GCP AoR) does not bear responsibility for the data provided. Users are
    encouraged to refer to the specific methodologies of each data source to understand the methods and appropriate use of
    the indicators provided.
    """
    )

    # Section: Disclaimer and Terms of Use
    _custom_title("Disclaimer and Terms of Use", font_size=30)
    st.markdown(
        """
    The information provided on this platform is for informational purposes only.
    The Global Child Protection Area of Responsibility (GCP AoR) makes no representations or warranties,
    expressed or implied, regarding the accuracy, completeness, or suitability for any particular purpose
    of the information available. The GCP AoR is not liable for any loss, damage, or liability
    arising from the use of this platform, and all use is at the user’s own risk.
    """
    )

    # Section: Content and Updates
    _custom_title("Content and Updates", 24)
    st.markdown(
        """
    The GCP AoR may update or modify content on this platform without notice. Users are advised not to rely solely
    on the information provided here for critical decisions.
    """
    )

    # Section: Third-Party Links and Information
    _custom_title("Third-Party Links and Information", 24)
    st.markdown(
        """
    This platform may include links to third-party websites and may contain advice, opinions,
    and statements from external providers. Reliance upon any such advice, opinion, statement,
    or other information shall also be at the User’s own risk. The GCP AoR does not control and
    is not responsible for the content or accuracy of these external sites. Links to third-party
    sites do not imply endorsement by the GCP AoR.
    """
    )

    # Section: Geographical and Political Information
    _custom_title("Geographical and Political Information", 24)
    st.markdown(
        """
    The presentation of geographical or political information does not imply endorsement by the GCP AoR.
    Terms like "country" refer generally to regions as appropriate, without assumptions regarding
    legal status or boundaries.
    """
    )

    # Section: NLP and AI-Generated Content
    _custom_title("NLP and AI-Generated Content", 24)
    st.markdown(
        """
    Content generated by Natural Language Processing (NLP) and AI (Artificial Intelligence)
    technologies is incorporated to enhance accessibility and understanding. However, this AI-generated
    content may contain inaccuracies or omissions and is not guaranteed for accuracy. Users should exercise
    caution and consult additional sources when making important decisions based on this content.
    The GCP AoR disclaims all liability for any errors in AI-generated content and reserves the right
    to modify or remove such content at any time.

    By using this platform, you acknowledge and agree to these terms.
    """
    )

    # Section: Contact
    _custom_title("Contact", 24)
    st.markdown(
        """
    [Contact the GCP AoR IM Team](mailto:SWZ-gcpaor-data-unit@unicef.org) for any additional question.
    """
    )
