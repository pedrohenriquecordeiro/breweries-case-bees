# Terraform Infrastructure for the Bees Data Platform

This folder contains Terraform code to provision and manage the core infrastructure for the Bees data platform on Google Cloud Platform (GCP). It automates the setup of networking, IAM, GKE clusters, storage buckets and other essential resources required for running data workflows and analytics workloads.

## Key Components

- **Terraform:** Infrastructure as code tool for declarative cloud resource management.
- **Google Cloud Platform (GCP):** Provides compute, storage and managed Kubernetes (GKE).
- **GKE (Google Kubernetes Engine):** Hosts Airflow, Spark Operator and other containerized workloads.
- **Google Cloud Storage (GCS):** Stores data, Airflow DAGs and logs.
- **IAM:** Manages service accounts and permissions for secure operations.

## Usage

1. Set your GCP project and region in `variables.tf` or via environment variables.
   - Important: Run the following command to set environment variables:
     ```sh
     export $(grep -v '^#' infra/.env | xargs)
     ```
2. Initialize Terraform and review the plan:
   ```sh
   terraform init
   terraform -chdir=infra/terraform plan
   ```
3. Apply the configuration to provision resources:
   ```sh
   terraform -chdir=infra/terraform apply --auto-approve
   ```

Refer to the main project README for prerequisites and environment setup.