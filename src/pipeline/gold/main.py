import sys
import os
import logging
import requests
from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.utils import AnalysisException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

if __name__ == "__main__":
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/.secrets/gke-service-account.json"

    spark = (
        SparkSession.builder
        .appName("ETL Silver Job")
        .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
        .config("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.databricks.delta.retentionDurationCheck.enabled", "false")
        .config("spark.dynamicAllocation.enabled", "true")
        .config("spark.dynamicAllocation.shuffleTracking.enabled", "true") 
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )

    # ------------------------------------------------------------------------------
    # Define GCS paths for silver and gold layers
    # ------------------------------------------------------------------------------
    silver_path = "gs://bees-storage/silver/"
    gold_path = "gs://bees-storage/gold/"

    # ------------------------------------------------------------------------------
    # Read silver Delta table from GCS
    # ------------------------------------------------------------------------------
    df_silver = spark.read.format("delta").load(silver_path)
    df_silver.createOrReplaceTempView("silver")

    # ------------------------------------------------------------------------------
    # Aggregate brewery counts by type, country, state and city
    # ------------------------------------------------------------------------------
    aggregated_df = spark.sql("""
        SELECT
            brewery_type,
            country,
            state,
            city,
            COUNT(*) AS brewery_count
        FROM 
            silver
        GROUP BY 
            country, state, city, brewery_type
    """)
    aggregated_df = aggregated_df.withColumn("update_at", current_timestamp())

    # ------------------------------------------------------------------------------
    # Write aggregated data to gold Delta table (overwrite mode)
    # ------------------------------------------------------------------------------
    if aggregated_df.rdd.isEmpty():
        logging.info("No new records to append.")
        
    else:
        (
            aggregated_df
                .write
                .format("delta")
                .option("mergeSchema", "true")
                .mode("overwrite")
                .save(gold_path)
        )
        logging.info("Appended new records to gold table.")

    spark.stop()