# Breweries Case

**Breweries Case** is a modular, cloud-native data platform for ingesting, processing, validating and analyzing brewery data at scale. Built on Google Cloud Platform (GCP), it leverages a layered Data Lakehouse architecture (Bronze, Silver, Gold) and orchestrates ETL workflows using Apache Airflow and Spark on Kubernetes.

## 🚀 Quick Start (Automated Setup)

The project includes a comprehensive setup script (`start.sh`) that automates the entire environment provisioning and deployment process.

### Using `start.sh`

This script is designed to handle everything from dependency checks to Airflow deployment:
1.  **Validates** your local environment (GCP CLI, Terraform, Docker, Helm).
2.  **Provisions** all necessary GCP infrastructure (GKS, GKE, Artifact Registry) using Terraform.
3.  **Builds and Pushes** custom Docker images for each part of the pipeline.
4.  **Deploys Apache Airflow** and the **Spark Operator** to the GKE cluster.
5.  **Configures** Workload Identity, RBAC and storage permissions.

Before starting, ensure you are authenticated with Google Cloud and have the correct project selected.
Create a new project or select an existing one and link the project to your billing account.

Then run the following commands:
```bash
gcloud init --project=dev-data-487517
gcloud auth application-default login
```

```bash
# Ensure you have an infra/.env file configured
chmod +x start.sh
./start.sh
```

## 📖 In-Depth Documentation

For detailed information about each component of the platform, please refer to the following guides in the `docs/` directory:

*   **[Architecture Overview](docs/architecture.md)**: Cloud-native design and Medallion architecture.
*   **[Orchestration](docs/orchestration.md)**: Details on Airflow and Spark Operator on GKE.
*   **[Bronze Layer](docs/bronze_layer.md)**: Raw API ingestion and storage.
*   **[Silver Layer](docs/silver_layer.md)**: Data curation and Delta Lake upserts.
*   **[Data Quality Tests](docs/data_quality_tests.md)**: Validation framework using PyDeequ.
*   **[Gold Layer](docs/gold_layer.md)**: Analytical aggregations for consumption.

## 📂 Repository Structure

```
breweries-case/
├── start.sh                      # Unified project setup script
├── docs/                         # Detailed component documentation
├── infra/                        # Infrastructure-as-code (Terraform) and K8s manifests
├── src/
│   ├── pipeline/                 # Core ETL and validation source code
│   │   ├── bronze/               # API Ingestion (Python)
│   │   ├── silver/               # Curation & Upsert (Spark/Delta)
│   │   ├── gold/                 # Aggregation (Spark/Delta)
│   │   ├── tests/                # Quality Validation (PyDeequ/Spark)
│   │   └── dag.py                # Main Airflow DAG definition
└── readme.md                     # You are here
```

## 🛠️ Technology Stack

*   **Cloud infrastructure**: GCP (GKE, GCS, Artifact Registry).
*   **Infrastructure-as-Code**: Terraform.
*   **Orchestration**: Apache Airflow.
*   **Processing**: Apache Spark & Delta Lake.
*   **Data Quality**: PyDeequ.
*   **Deployment**: Docker, Helm, Kubernetes.
