# Silver Layer (Curated)

The **Silver Layer** transforms raw bronze data into a cleansed, curated and optimized Delta Lake table.

## Processing Logic

The transformation is powered by **Apache Spark**, with the main script located at `src/pipeline/silver/main.py`.

### Key Features

*   **Latest Data Retrieval**: Automatically identifies the most recent timestamped folder in the bronze layer to ensure it processes the latest ingestion.
*   **Schema Enforcement**: Casts raw API strings into appropriate data types (Strings, Doubles, etc.).
*   **Upsert (MERGE) Pattern**: Uses Delta Lake's `MERGE` capability to perform upserts based on the brewery `id`. This ensures that existing records are updated and new ones are inserted without duplication.
*   **Ingestion Metadata**: Adds an `ingestion_at` timestamp to every record for Auditability.

## Storage & Partitioning

*   **Location**: `gs://bees-storage/silver/`
*   **File Format**: Delta Lake (Parquet-based with ACID transaction logs).
*   **Partitioning**: The table is partitioned by `country`, `state` and `city` to optimize query performance and data pruning.

## In-Cluster Execution

The Silver layer runs as a `SparkApplication` triggered by the `SparkKubernetesOperator`. It leverages dynamic allocation to scale executors based on the workload size.
