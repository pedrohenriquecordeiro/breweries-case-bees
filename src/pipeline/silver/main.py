import sys
import logging
from datetime import datetime
from google.cloud import storage

from delta.tables import DeltaTable
from pyspark.sql import SparkSession
from pyspark.sql.functions import current_timestamp
from pyspark.sql.utils import AnalysisException

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def latest_gcs_folder(bucket: str, prefix: str, fmt: str = "%Y-%m-%dT%H-%M-%S"):
    client = storage.Client()
    blobs = client.list_blobs(bucket, prefix=prefix, delimiter="/")
    folders = []
    for page in blobs.pages:
        for p in page.prefixes:
            name = p.rstrip("/").split("/")[-1]
            try:
                folders.append((datetime.strptime(name, fmt), p))
            except ValueError:
                pass
    return max(folders)[1] if folders else None


if __name__ == "__main__":
    spark = (
        SparkSession.builder
        .appName("ETL Silver Job (Upsert)")
        .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
        .config("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.databricks.delta.retentionDurationCheck.enabled", "false")
        .config("spark.dynamicAllocation.shuffleTracking.enabled", "true")
        .config("spark.sql.adaptive.enabled", "true")
        .getOrCreate()
    )

    bronze_bucket = "bees-storage"
    bronze_base_prefix = "bronze/data/"
    silver_path = "gs://bees-storage/silver/"

    latest_prefix = latest_gcs_folder(bronze_bucket, bronze_base_prefix)
    if not latest_prefix:
        logging.error(f"No timestamped folders found under gs://{bronze_bucket}/{bronze_base_prefix}")
        sys.exit(1)

    bronze_path = f"gs://{bronze_bucket}/{latest_prefix}"
    logging.info(f"Using latest bronze folder: {bronze_path}")

    # -------------------- Read bronze --------------------
    try:
        df_bronze = spark.read.option("multiLine", True).json(bronze_path)
        df_bronze.createOrReplaceTempView("bronze")
    except AnalysisException as e:
        logging.error(f"Bronze path not found or unreadable at {bronze_path}: {e}")
        sys.exit(1)

    df_bronze.printSchema()

    # -------------------- Ensure silver exists --------------------
    try:
        DeltaTable.forPath(spark, silver_path)
        logging.info("Silver Delta table found.")
    except AnalysisException:
        logging.warning(f"Silver Delta table not found at {silver_path}. Initializing.")
        (spark.createDataFrame([], df_bronze.schema)
             .write.format("delta")
             .mode("overwrite")
             .partitionBy("country", "state", "city")
             .save(silver_path))

    silver_dt = DeltaTable.forPath(spark, silver_path)

    # -------------------- Build staged (casted) source --------------------
    staged_df = spark.sql("""
        SELECT
            CAST(id             AS STRING) AS id,
            CAST(name           AS STRING) AS name,
            CAST(brewery_type   AS STRING) AS brewery_type,
            CAST(address_1      AS STRING) AS address_1,
            CAST(address_2      AS STRING) AS address_2,
            CAST(address_3      AS STRING) AS address_3,
            CAST(city           AS STRING) AS city,
            CAST(state_province AS STRING) AS state_province,
            CAST(postal_code    AS STRING) AS postal_code,
            CAST(country        AS STRING) AS country,
            CAST(longitude      AS DOUBLE) AS longitude,
            CAST(latitude       AS DOUBLE) AS latitude,
            CAST(phone          AS STRING) AS phone,
            CAST(website_url    AS STRING) AS website_url,
            CAST(state          AS STRING) AS state,
            CAST(street         AS STRING) AS street
        FROM bronze
    """).withColumn("ingestion_at", current_timestamp()) \
      .repartition("country", "state", "city")

    # -------------------- UPSERT (MERGE) by id --------------------
    if staged_df.take(1):
        logging.info("Running MERGE upsert into silver by id...")
        (silver_dt.alias("t")
            .merge(
                staged_df.alias("s"),
                "t.id = s.id"
            )
            .whenMatchedUpdateAll()
            .whenNotMatchedInsertAll()
            .execute())
        logging.info("Upsert completed.")
    else:
        logging.info("No records found in bronze to upsert.")

    spark.stop()
