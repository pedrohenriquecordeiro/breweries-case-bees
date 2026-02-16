# Bronze Layer (Raw)

The **Bronze Layer** is responsible for the initial ingestion of raw data from the **Open Brewery DB API** into Google Cloud Storage.

## Ingestion Process

The ingestion script is located at `src/pipeline/bronze/main.py` and is executed as an Airflow-native task.

### Key Features

*   **API Pagination**: Handles large volumes of data by iterating through API pages (up to 1,000 pages).
*   **Load Types**:
    *   **Full Load**: Running for the first time or when no metadata is found.
    *   **Incremental Load**: Uses a `max_id` stored in a metadata JSON file to fetch only new records.
*   **Retry Logic**: Implements exponential backoff for failed API requests to handle intermittent network issues.
*   **Safety Limits**: Includes a `MAX_PAGES` safety limit and `API_TIMEOUT` to prevent runaway processes.

## Storage Strategy

*   **Location**: `gs://bees-storage/bronze/data/`
*   **File Format**: Standard JSON.
*   **Organization**: Data is stored in timestamped subdirectories to facilitate troubleshooting and point-in-time recovery.
    *   Example: `bronze/data/2026_02_15_23_29_27_000000/12345.json`

## Metadata

A metadata file (`bronze/metadata/metadata.json`) tracks the high-water mark (`max_id`) of ingested breweries and the last ingestion timestamp. This file is essential for the incremental loading logic.

## Usage

The Bronze layer can be executed independently through the `run_bronze_pipeline()` function, provided the `BUCKET_NAME` environment variable is set.
