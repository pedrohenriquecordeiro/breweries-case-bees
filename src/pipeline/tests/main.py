import logging, os, sys

from pyspark.sql import SparkSession
from pyspark.sql.types import DoubleType, StringType, TimestampType

from pydeequ.verification import *
from pydeequ.checks import *
from pydeequ.repository import *
from pydeequ.analyzers import *


if __name__ == "__main__":
    
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/app/.secrets/gke-service-account.json"
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )
    logger = logging.getLogger(__name__)

    # ------------------------------------------------------------------------------
    # Expected schema definition
    # ------------------------------------------------------------------------------
    EXPECTED_SCHEMA = {
        "address_1"     : StringType(),
        "address_2"     : StringType(),
        "address_3"     : StringType(),
        "brewery_type"  : StringType(),
        "city"          : StringType(),
        "country"       : StringType(),
        "id"            : StringType(),
        "latitude"      : DoubleType(),
        "longitude"     : DoubleType(),
        "name"          : StringType(),
        "phone"         : StringType(),
        "postal_code"   : StringType(),
        "state"         : StringType(),
        "state_province": StringType(),
        "street"        : StringType(),
        "website_url"   : StringType(),
        "ingestion_at"  : TimestampType()
    }


    logger.info("Initializing Spark session with Delta support...")
    
    spark = (
        SparkSession.builder \
        .appName("Delta Data Quality Checks")
        .config("spark.sql.parquet.datetimeRebaseModeInRead", "CORRECTED")
        .config("spark.sql.parquet.datetimeRebaseModeInWrite", "CORRECTED")
        .config("spark.hadoop.fs.gs.impl", "com.google.cloud.hadoop.fs.gcs.GoogleHadoopFileSystem")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
        .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
        .getOrCreate()
    )

    logger.info("Spark session started.")

    # ------------------------------------------------------------------------------
    # Load data: Delta from GCS
    # ------------------------------------------------------------------------------
    silver_path = "gs://bees-storage/silver/"
    logger.info(f"Loading Delta data from: {silver_path}")
    
    df_silver = spark.read.format("delta").load(silver_path)
    logger.info(f"Loaded {df_silver.count()} records.")

    # ------------------------------------------------------------------------------
    # Schema validation
    # ------------------------------------------------------------------------------
    logger.info("Validating schema...")
    
    # Validate schema: check field names and types
    schema_mismatches = []
    
    for field, expected_type in EXPECTED_SCHEMA.items():
        
        if field not in df_silver.schema.fieldNames():
            schema_mismatches.append(f"Missing field: {field}")
            
        else:
            actual_type = dict((f.name, f.dataType) for f in df_silver.schema)[field]
            
            if type(actual_type) != type(expected_type):
                schema_mismatches.append(
                    f"Type mismatch for '{field}': expected {expected_type}, got {actual_type}"
                )
                
    extra_fields = set(df_silver.schema.fieldNames()) - set(EXPECTED_SCHEMA.keys())
    
    for field in extra_fields:
        schema_mismatches.append(f"Unexpected extra field: {field}")

    if schema_mismatches:
        logger.error("Schema validation failed:")
        for msg in schema_mismatches:
            logger.error(msg)
        sys.exit(1)
        
    else:
        logger.info("Schema validation passed: all fields and types match EXPECTED_SCHEMA.")
    
    # ------------------------------------------------------------------------------
    # Deequ verification suite
    # ------------------------------------------------------------------------------
    logger.info("Running Deequ verification suite...")
    
    check = Check(spark, CheckLevel.Error, "Data quality checks")
    
    verification = (
        VerificationSuite(spark)
        .onData(df_silver)
        .addCheck(
            check
            .isUnique("id")
            .isComplete("id")
            .isComplete("name")
            .isComplete("brewery_type")
            .isComplete("city")
            .isComplete("country")
            .isComplete("state")
            .isComplete("postal_code")
            .hasDataType("id"        , ConstrainableDataTypes.String)
            .hasDataType("country"   , ConstrainableDataTypes.String)
            .hasDataType("state"     , ConstrainableDataTypes.String)
            .hasDataType("city"      , ConstrainableDataTypes.String)
            .hasDataType("latitude"  , ConstrainableDataTypes.Fractional)
            .hasDataType("longitude" , ConstrainableDataTypes.Fractional)
        )
    )
    
    logger.info("Verification suite configured.")
    result = verification.run()

    # ------------------------------------------------------------------------------
    # Print summary
    # ------------------------------------------------------------------------------
    res_df = VerificationResult.checkResultsAsDataFrame(spark, result)
    
    logger.info("Deequ check results:")
    res_df.show(truncate = False)
    
    # ------------------------------------------------------------------------------
    # Exit logic based on status
    # ------------------------------------------------------------------------------
    if result.status != "Success":
        logger.error("Data quality failed.")
        sys.exit(1)
        
    else:
        logger.info("Data quality passed.")

    logger.info("Stopping Spark session.")
    spark.stop()