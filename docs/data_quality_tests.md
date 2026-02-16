# Data Quality Tests

Data quality is a core pillar of the **Breweries Case** platform. We use **PyDeequ** (a Python wrapper for Deequ, built on Spark) to perform automated validation on our Silver layer data.

## Deequ Configuration

The testing process is configured using the PyDeequ `VerificationSuite`. The configuration involves:

1.  **Spark Session with Delta Support**: The job initializes a Spark session configured to read Delta Lake tables from GCS.
2.  **Verification Suite**: A `VerificationSuite` is initialized on the Silver DataFrame.
3.  **Check Object**: A `Check` object is defined with `CheckLevel.Error`. This means that if any constraint is not met, the entire suite will return a failure status.
4.  **Constraint Definition**: Multiple constraints (Completeness, Uniqueness, DataType) are chained to the check object.
5.  **Execution & Result Analysis**: The `run()` method executes the checks. Results are converted to a DataFrame for logging and the script exits with code `1` if the state is not "Success".

## Column Selection Rationale

The following columns are prioritized for validation to ensure the integrity of the Data Lakehouse:

| Column | Constraint | Rationale |
| :--- | :--- | :--- |
| **`id`** | Unique, Complete | Primary key for the dataset. Uniqueness and completeness are critical for the **Upsert (Merge)** logic in the Silver layer and to prevent record duplication. |
| **`name`** | Complete | Essential for identifying the brewery in any analytical report or dashboard. |
| **`brewery_type`** | Complete | A key dimension for categorical analysis. Nulls would degrade the value of business intelligence reports. |
| **`country`, `state`, `city`** | Complete | These are the **Partition Columns** for the Silver layer. Completeness ensures that data is correctly distributed in GCS and query pruning works efficiently. |
| **`postal_code`** | Complete | Important for granular geospatial analysis and regional mailing/contact reporting. |
| **`latitude`, `longitude`** | DataType (Fractional) | Crucial for mapping and GIS applications. Enforcing the `Double` type ensures that mathematical operations on coordinates don't fail downstream. |

## Validation Workflow

1.  **Read Silver Data**: The test job reads the curated Silver Delta table.
2.  **Execute Analysis**: PyDeequ runs the suite of checks against the DataFrame.
3.  **Verification Result**:
    *   If all checks pass, the job completes successfully, allowing the pipeline to proceed to the Gold layer.
    *   If any check fails, the job raises an exception and the Airflow DAG is marked as failed, preventing low-quality data from reaching the analytical layer.
