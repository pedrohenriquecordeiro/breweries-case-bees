# Breweries-Case Project: Step-by-Step Reproducible Guide

This guide provides a detailed walkthrough of all critical setup and execution steps for the `breweries-case` project.

### Required GCP Permissions to set up the project

If you're bootstrapping quickly, assigning the following roles is usually sufficient:
 - `roles/resourcemanager.projectCreator` (to create projects)
 - `roles/billing.user` (to link to billing)
 - `roles/owner` on the target project

Below is a breakdown of GCP IAM roles and permissions needed to set up and run the project:


| **Recommended IAM Role(s)**                            | **Key Permissions**                                                                 |
|--------------------------------------------------------|--------------------------------------------------------------------------------------|
| `roles/resourcemanager.projectCreator`                 | `resourcemanager.projects.create`                                                   |
| `roles/billing.user`                                   | `billing.resourceAssociations.create`                                               |
| `roles/viewer` or `roles/resourcemanager.projectViewer`| `resourcemanager.projects.get`, `resourcemanager.projects.list`                     |
| `roles/iam.serviceAccountKeyAdmin`                     | `iam.serviceAccountKeys.create`, `iam.serviceAccountKeys.list`                      |
| `roles/iam.serviceAccountAdmin`                        | `iam.serviceAccounts.setIamPolicy`, `iam.serviceAccounts.actAs`                     |
| `roles/iam.workloadIdentityUser`                       | `iam.serviceAccounts.setIamPolicy`, `iam.serviceAccounts.actAs`                     |
| `roles/storage.objectAdmin`                            | `storage.objects.create`, `storage.objects.get`, `storage.objects.list`             |
| `roles/artifactregistry.writer`                        | `artifactregistry.repositories.uploadArtifacts`, `artifactregistry.repositories.get`|
| `roles/container.clusterViewer`                        | `container.clusters.get`, `container.clusters.getCredentials`                       |
| `roles/container.developer` + Kubernetes RBAC          | `container.*` API access + Kubernetes cluster-admin (or scoped) permissions         |
| `roles/owner` (for Terraform bootstrap)                | Varies: permissions for GKE, IAM, Storage, Artifact Registry, etc.                  |




## 1. GCloud Login

Before starting, ensure you are authenticated with Google Cloud and have the correct project selected.

Create a new project or select an existing one. Link the project to your billing account.
Do it by console.

```bash
gcloud init --project=dev-data-487517
gcloud auth application-default login
```


## 2. Load Environment Variables

Write a **temporary** `.env` file in the `infra` directory with the following content:

```bash
PROJECT_ID=<your-gcp-project-id>
TF_VAR_project_id=<your-gcp-project-id>
```

Load the environment variables:

```bash
export $(grep -v '^#' infra/.env | xargs)
```

## 3. Enable Required APIs

Enable the necessary Google Cloud APIs for the project. This is essential for using services like Artifact Registry, Compute Engine and Storage.

```bash
gcloud services enable artifactregistry.googleapis.com --project=$PROJECT_ID
gcloud services enable compute.googleapis.com --project=$PROJECT_ID
gcloud services enable storage.googleapis.com --project=$PROJECT_ID
gcloud services enable container.googleapis.com --project=$PROJECT_ID
```

## 4. Install Google Cloud SDK

Install the Google Cloud SDK to interact with GCP services. This is required for managing GCP resources, authenticating and deploying applications.

```bash
brew install --cask google-cloud-sdk
```

**Dependencies:** Homebrew (macOS), curl (Linux).

## 5. Initialize and Authenticate with Google Cloud

```bash
gcloud components install gke-gcloud-auth-plugin
gcloud components update
```
- `gcloud init`: Set up project and authentication.
- `auth login`: Authenticate your user.
- `components install`: Required for GKE cluster authentication.

## 6. Install Developer Tools

Install Terraform, kubectl, kubectx and Helm.

```bash
# macOS
brew tap hashicorp/tap
brew install hashicorp/tap/terraform
brew install kubectl
brew install kubectx
brew install helm

# Linux : search how to install Terraform, kubectl, kubectx and Helm
```

## 7. Go to Project Root Directory

```bash
cd breweries-case
```

## 8. Provision Infrastructure with Terraform

Initialize and deploy infrastructure as code.

```bash
terraform -chdir=infra/terraform init
terraform -chdir=infra/terraform plan
terraform -chdir=infra/terraform apply --auto-approve
```

This step takes about 15 minutes to complete.

## 9. Create and Distribute GKE Service Account Key

Create and distribute a service account key across different pipeline components. You need the necessary permissions to create service accounts and keys in your GCP project.

```bash
gcloud iam service-accounts keys create src/pipeline/bronze/gke-service-account.json --iam-account=gke-service-account@$PROJECT_ID.iam.gserviceaccount.com
cp src/pipeline/bronze/gke-service-account.json src/pipeline/silver/
cp src/pipeline/bronze/gke-service-account.json src/pipeline/gold/
cp src/pipeline/bronze/gke-service-account.json src/pipeline/tests/
```

## 10. Configure Docker for Artifact Registry

Allow Docker to authenticate and push images to GCP Artifact Registry.

```bash
gcloud auth configure-docker us-central1-docker.pkg.dev
```

## 11. Build and Push Docker Images

Build and push Docker images for each ETL pipeline (bronze, silver, gold) and tests.

```bash
docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/$PROJECT_ID/bees-docker-repo/bronze/bees-etl-bronze-job:latest \
  --push src/pipeline/bronze/

docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/$PROJECT_ID/bees-docker-repo/silver/bees-etl-silver-job:latest  \
  --push src/pipeline/silver/

docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/$PROJECT_ID/bees-docker-repo/gold/bees-etl-gold-job:latest \
  --push src/pipeline/gold/

docker buildx build --platform linux/amd64 \
  -t us-central1-docker.pkg.dev/$PROJECT_ID/bees-docker-repo/tests/bees-test-data-quality:latest \
  --push src/pipeline/tests/
```

This step takes about 15 minutes to complete.

## 12. Upload Airflow DAGs to GCS

Before uploading the DAG code, edit `src/dags/dag.py` to set the correct project ID. After editing, copy Airflow DAGs to the DAGs bucket.

```bash
# macOS
cp src/dags/dag.py /tmp/dag.py
sed -i '' 's/<your-gcp-project-id>/'"$PROJECT_ID"'/g' /tmp/dag.py
gsutil cp /tmp/dag.py gs://bees-airflow-dags/
rm /tmp/dag.py

# Linux
cp src/dags/dag.py /tmp/dag.py
sed -i 's/<your-gcp-project-id>/'"$PROJECT_ID"'/g' /tmp/dag.py
gsutil cp /tmp/dag.py gs://bees-airflow-dags/
rm /tmp/dag.py
```

## 13. Configure GKE Context

Connect to the cluster and create the namespace.

```bash
gcloud container clusters get-credentials airflow-cluster --zone us-central1-c --project $PROJECT_ID
```

## 14. Apply Secrets and Permissions for Airflow

Set up secrets and role bindings required for Airflow.

```bash
kubectl create namespace airflow
kubectl create secret generic gke-service-account-secret \
  --from-file=key.json=src/pipeline/silver/gke-service-account.json \
  -n airflow
kubectl apply -f infra/kubernetes/airflow/manifests/rbac.yaml
```

## 15. Grant Storage Access to GSA (Google Service Account)

Allow Airflow access to read/write logs, DAGs and data in GCS.

```bash
gcloud storage buckets add-iam-policy-binding gs://bees-airflow-logs \
  --member="serviceAccount:gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud storage buckets add-iam-policy-binding gs://bees-airflow-dags \
  --member="serviceAccount:gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"

gcloud storage buckets add-iam-policy-binding gs://bees-storage \
  --member="serviceAccount:gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.objectAdmin"
```

## 16. Configure Workload Identity (Airflow)

Allow Airflow to use the GKE service account for Google Cloud API access.

```bash
gcloud iam service-accounts add-iam-policy-binding \
  gke-service-account@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[airflow/airflow-service-account]"

kubectl annotate serviceaccount \
  airflow-service-account \
  --namespace airflow \
  iam.gke.io/gcp-service-account=gke-service-account@$PROJECT_ID.iam.gserviceaccount.com
```

## 17. Configure Persistent Volumes for DAGs and Logs

Set up persistent volumes using GCS Fuse for Airflow DAGs and logs.

```bash
kubectl apply -f infra/kubernetes/airflow/manifests/pv-gcs-fuse-dags.yaml
kubectl apply -f infra/kubernetes/airflow/manifests/pvc-gcs-fuse-dags.yaml
kubectl apply -f infra/kubernetes/airflow/manifests/pv-gcs-fuse-logs.yaml
kubectl apply -f infra/kubernetes/airflow/manifests/pvc-gcs-fuse-logs.yaml
```

## 18. Install Airflow via Helm

```bash
helm repo add apache-airflow https://airflow.apache.org/ --force-update

helm upgrade --install airflow apache-airflow/airflow \
  --version 1.16.0 \
  -f infra/kubernetes/airflow/manifests/values_helm.yaml \
  --namespace airflow \
  --set config.smtp.smtp_password="$SMTP_PASSWORD"
```
This steps takes about 10 minutes to complete.

## 19. Add Airflow Kubernetes Connection

Add a Kubernetes in-cluster connection for Airflow.

```bash
kubectl exec -it $(kubectl get pod -n airflow -l "component=webserver" -o jsonpath="{.items[0].metadata.name}") -n airflow -- \
    airflow connections add in_cluster_configuration_kubernetes_cluster \
    --conn-type kubernetes \
    --conn-extra '{"in_cluster": true}'
```

## 20. Set Up Spark Operator

Deploy Spark Operator for running Spark jobs.

```bash
kubectl create namespace spark
kubectl apply -f infra/kubernetes/spark-operator/rbac.yaml
helm repo add spark-operator https://kubeflow.github.io/spark-operator --force-update
helm upgrade --install spark-operator spark-operator/spark-operator \
  --wait \
  -f infra/kubernetes/spark-operator/values_helm.yaml \
  --namespace spark
```

## 21. Configure Workload Identity (Spark)

Allow Spark jobs to use the GKE service account for Google Cloud API access.

```bash
gcloud iam service-accounts add-iam-policy-binding \
  gke-service-account@$PROJECT_ID.iam.gserviceaccount.com \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[spark/spark-service-account]"

kubectl annotate serviceaccount \
  spark-service-account \
  --namespace spark \
  iam.gke.io/gcp-service-account=gke-service-account@$PROJECT_ID.iam.gserviceaccount.com
```

## 22. Access Airflow Web UI

Make the Airflow UI available at [http://localhost:8080](http://localhost:8080)

```bash
kubectl port-forward svc/airflow-webserver 8080:8080 --namespace airflow
```

To log in, use username and password: `bees`.

## 23. Run Airflow DAG

> **Alert:**  
> Before running the DAG, check your GCP project quotas—especially for the Compute Engine API (C2D CPUs, CPUs (all regions), Persistent Disk SSD (GB), etc.). If you exceed quota limits, the cluster may not scale up, causing the DAG to fail or run slowly.  
> Review your quotas at [https://console.cloud.google.com/iam-admin/quotas](https://console.cloud.google.com/iam-admin/quotas) and keep looking at it during the DAG execution.

Open the Airflow UI at [http://localhost:8080](http://localhost:8080) and trigger the DAG `data-pipeline-breweries`. You can monitor the execution of the DAG and check the logs for each task.

To see the pods created by the DAG, run:

```bash
kubectl get pods -n airflow --watch
kubectl get pods -n spark --watch
```

The first run may take about 25 minutes to complete, but subsequent runs will be faster as the data is already partitioned.



## 24. Check Results

After the DAG execution is complete, you can check the results in the GCS buckets using the notebook in `src/notebooks/show.ipynb`. There is pre-written code to show the results of the silver and gold pipelines.

To check the results of test data quality you can see the logs of the task in airflow, or download the results from the GCS bucket `gs://bees-airflow-logs/`. If the task fails, an email will be sent to the configured SMTP server with the error details.

## 25. Clean Up Resources
To clean up all resources created during the setup, run:

```bash
terraform -chdir=infra/terraform destroy --auto-approve
```

If some error message just run the command again, it will delete all resources created by Terraform.

After running the command, you can also delete the GCP project if you no longer need it:

```bash
gcloud projects delete <your-gcp-project-id>
```