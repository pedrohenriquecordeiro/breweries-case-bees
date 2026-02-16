from datetime import timedelta
import pendulum
from airflow.decorators import dag, task
from airflow.operators.dummy_operator import DummyOperator
from airflow.providers.cncf.kubernetes.operators.spark_kubernetes import SparkKubernetesOperator
from kubernetes.client import models as k8s

# Import the refactored bronze pipeline logic
from bronze.main import run_bronze_pipeline

PROJECT_ID = "<your-gcp-project-id>"  # Replace with your GCP project ID

# Docker images for each stage of the ETL process
silver_image            = f"us-central1-docker.pkg.dev/{PROJECT_ID}/bees-docker-repo/silver/bees-etl-silver-job:latest"
gold_image              = f"us-central1-docker.pkg.dev/{PROJECT_ID}/bees-docker-repo/gold/bees-etl-gold-job:latest"
test_data_quality_image = f"us-central1-docker.pkg.dev/{PROJECT_ID}/bees-docker-repo/tests/bees-test-data-quality:latest"

# Default arguments for the DAG
DEFAULT_ARGS = {
  "owner"            : "Pedro Jesus",
  "start_date"       : pendulum.datetime(2026, 2, 15, tz = pendulum.timezone("America/Sao_Paulo")),
  "email"            : ["pedrohcordeiroj@gmail.com"],
  "email_on_failure" : True,
  "email_on_retry"   : True,
  "max_active_runs"  : 1,
  "retries"          : 3,
  "retry_delay"      : timedelta(minutes = 1)
}

# SparkApplication manifest template for SparkKubernetesOperator
SPARK_APPLICATION_MANIFEST = '''
  apiVersion: sparkoperator.k8s.io/v1beta2
  kind: SparkApplication
  metadata:
    name: spark-job                            # Name of the Spark application
    namespace: spark                           # Kubernetes namespace
  spec:
    type: Python                               # Type of Spark job
    pythonVersion: "3"
    sparkVersion: "3.5.3"                      # Spark version to use
    mode: cluster                              # Run in cluster mode
    image: {IMAGE_SPARK}                       # Docker image with your Spark job
    imagePullSecrets:
      - gke-service-account-secret
    imagePullPolicy: Always                    # Always pull image (only for development)
    mainApplicationFile: local:///app/main.py  # Entry point for your Spark app
    driver:
      serviceAccount: spark-service-account
      coreRequest: 500m                        # CPU request for the driver
      coreLimit: 2000m                         # CPU limit for the driver
      memory: 4096m
      labels:
        app: spark-driver
    executor:
      serviceAccount: spark-service-account
      coreRequest: 500m
      coreLimit: 2000m
      memory: 4096m
      labels:
        app: spark-executor
    dynamicAllocation:
      enabled: true
      initialExecutors: 1
      minExecutors: 1
      maxExecutors: 5
'''

@dag(
  dag_id            = "data-pipeline-breweries",
  default_args      = DEFAULT_ARGS,
  schedule_interval = "@once",
  catchup           = False,
  tags              = ["bees"],
)
def pipeline_dag():
  # Dummy start task
  start = DummyOperator(task_id="start")

  # Bronze layer: Run ETL job using Airflow-native Python capabilities
  # Configured to use 'airflow-service-account' for Workload Identity
  bronze_task = run_bronze_pipeline.override(
    executor_config = {
      "pod_override": k8s.V1Pod(
        spec = k8s.V1PodSpec(
          service_account_name = "airflow-service-account"
        )
      )
    }
  )()

  # Silver layer: Run Spark job using SparkKubernetesOperator
  silver_task = SparkKubernetesOperator(
    task_id                 = "silver_task",
    namespace               = "spark",
    get_logs                = True,
    startup_timeout_seconds = 600,
    delete_on_termination   = True,
    application_file        = SPARK_APPLICATION_MANIFEST.replace("{IMAGE_SPARK}", silver_image),
    kubernetes_conn_id      = "in_cluster_configuration_kubernetes_cluster"
  )
  
  # Data quality test: Run Spark job for data quality checks
  test_data_quality = SparkKubernetesOperator(
    task_id                 = "test_data_quality",
    namespace               = "spark",
    get_logs                = True,
    startup_timeout_seconds = 600,
    delete_on_termination   = True,
    application_file        = SPARK_APPLICATION_MANIFEST.replace("{IMAGE_SPARK}", test_data_quality_image),
    kubernetes_conn_id      = "in_cluster_configuration_kubernetes_cluster"
  )
  
  # Gold layer: Run Spark job for gold layer ETL
  gold_task = SparkKubernetesOperator(
    task_id                 = "gold_task",
    namespace               = "spark",
    get_logs                = True,
    startup_timeout_seconds = 600,
    delete_on_termination   = True,
    application_file        = SPARK_APPLICATION_MANIFEST.replace("{IMAGE_SPARK}", gold_image),
    kubernetes_conn_id      = "in_cluster_configuration_kubernetes_cluster"
  )

  # Define task dependencies
  start >> bronze_task >> silver_task >> test_data_quality >> gold_task

pipeline_dag()