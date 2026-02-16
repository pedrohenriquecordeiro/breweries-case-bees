# Gold Layer (Analytical)

The **Gold Layer** is the final stage of the pipeline, providing highly optimized, aggregated data for analytical consumption.

## Business Logic

The aggregation logic is located at `src/pipeline/gold/main.py`.

### Aggregations

This layer consumes data from the Silver Delta table and produces analytical views, such as:
*   **Brewery Count by Type and Location**: Aggregates the number of breweries grouped by `brewery_type`, `country`, `state` and `city`.
*   **Regional Summaries**: Summarizes topological distribution of breweries.

## Storage & Format

*   **Location**: `gs://bees-storage/gold/`
*   **File Format**: Delta Lake.
*   **Purpose**: These tables are intended to be connected to BI tools (like Looker, Tableau, or Power BI) or queried directly via Spark for rapid analytical insights.

## Scalability

Like the Silver layer, the Gold layer runs as a Spark job on Kubernetes, ensuring it can handle large-scale aggregations efficiently using Spark's distributed processing and Delta Lake's optimized file layout.
