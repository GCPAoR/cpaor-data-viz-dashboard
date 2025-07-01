# CPAoR project

## - Repository structure
```
├── data                                         # data folder: contains all data needed to load the streamlit app.
│   ├── report_countries.csv                     # file containing all countries processed in the project
----------------------------------------------------------------------------------------------------------------
├── data_sources_processing_src                  # Folder containing data sources processing scripts, each subfolder contains scripts for a different data source.
|   ├── data_sources_processing                  # Folder containing data sources processing scripts, each subfolder contains scripts for a different data source.
|       ├── acaps_inform_severity                # ACAPS, INFORM Severity Index
|       ├── acaps_protection_indicators          # ACAPS, Protection Indicators
|       ├── acled                                # ACLED
|       ├── idmc                                 # IDMC
|       ├── ipc                                  # IPC
|       ├── ocha_hpc                             # OCHA HPC
|       ├── ohchr                                # OHCHR legal frameowork
|       |__ datasets_metadata.json               # .json file containing metadata about updating status of different datasets
|       |__ utils.py                             # utils functions for dataset updating
|   |── crontab                                  # cron configuration for scheduled task
|   |── Dockerfile                               # configuration file to create docker image
|   |── pyproject.toml                           # libraries dependency configuration
|   |── poetry.lock                              # libraries lock file
|   |── update_datasets.py                       # main script to update the datasets
----------------------------------------------------------------------------------------------------------------
├── frontend_src                                        # Folder containing the frontend scripts
|   ├── .streamlit                                      # contains passwords
│       ├── secrets.toml                                # contains streamlit secrets file
|   ├── frontend                                        # Folder containing the frontend scripts
|      ├── custom_pages                                 # Contains main pages pages displayed..
|          ├── country_wide_analysis                    # Scripts containing country-wise pages
|               |__ country_profile.py                  # COUNTRY PROFILE page script
|               |__ crisis_wise_analysis.py             # CRISIS-WISE page script
|           ├── worldwide_analysis                      # Scripts containing world-wide pages
|               |__ worldwide_analysis.py               # Script for first streamlit page: GLOBAL OVERVIEW
|           ├── images                                  # Contains util functions to be called in different pages.
|       ├── src                                         # Contains util functions to be called in different pages.
|           ├── authentification                        # Contains authentification scripts
|               |__ auth.py
|           ├── utils                                   # Contains util scripts, loaded across different scripts.
|               |__ load_geodata.py                     # Contains functions for loading geodata (worldwide and contry-wide)
|               |__ utils_functions.py                  # Contains util functions to be called in different pages.
|           ├── specific_datasets_scripts               # Contains scripts for each datasource, each datasource is processed in a different script for clarity.
|               |__ acaps_inform_severity.py            # ACAPS, INFORM Severity Index
|               |__ acled.py                            # ACLED
|               |__ idmc.py                             # IDMC
|               |__ ipc.py                              # IPC
|               |__ legal_framework_results_display.py  # OHCHR legal frameowork processing
|               |__ ocha_hpc.py                         # OCHA HPC
|               |__ protection_data_display.py          # ACAPS, Protection Indicators
|               |__ unicef_data_processing.py           # Unicef Global indicator database
|           ├── visualizations                          # Contains visualizations scripts
|               |__ barchart.py                         # Contains scripts containing visualizations with everything containing bars (stackbars, horizontal, vertical barcharts, ...)
|               |__ maps_creation.py                    # Contains scripts for maps creation (country-wide and worldwide)
|    ├── app.py                                         # Home page of the streamlit application, to be run to launch the app.
|    ├── Dockerfile                                     # configuration file to create docker image
|    ├── pyproject.toml                                 # libraries dependency configuration
|    ├── poetry.lock                                    # libraries lock file
----------------------------------------------------------------------------------------------------------------
├── docker-compose.yml                           # docker configuration main yaml file.
├── README.md                                    # Readme file, containing main informations about the project
```

Note 1: There are `.env.sample` files in both the directories `data_sources_processing_src` and `frontend_src`.
        Please copy those files and rename those files as `.env` and set the corresponding environment variables.

Note 2: The password of the streamlit application has to be set in this file `.streamlit/secrets.toml` or set Environment variable STREAMLIT_USER_PASSWORD in .env file.

Note 3: For the production deployment, those environment variables are maintained in Parameter Stores in AWS.


## - Dataset creation from scratch
#### 1. Data sources pulling and processing
In a shell, run `bash update_sources.sh`

#### 2. Geolocation data processing
Go the [Fieldmaps website](https://fieldmaps.io/data) and download the amin level boundaries for admin0 and admin1 levels. Name them `adm0_polygons.gpkg` and `adm1_polygons.gpkg` respectively. Place them in the folder `data/datasources/polygons_data`.

## - Image build and running the containers in local environment
### Build two images
`docker compose build`
### Run the image containers
`docker compose up -d`

`Note that the data sources need to be manually loaded in the docker container in the /data directory if you want to instantly visualize the contents in the dashboard.`

## - Streamlit app local access
`http://localhost:8501`
