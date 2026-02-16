#!/bin/bash

# ==============================================================================
# Breweries-Case Project: Automated Setup Script
# Description: Automates the entire project setup as described in docs/setup.md
# ==============================================================================

set -e # Exit on any command failure
set -o pipefail # Catch errors in piped commands

# --- Color and Emoji Definitions ---
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- Error Handling Trap ---
cleanup_on_error() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo -e "\n${RED}${BOLD}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!${NC}"
        log_error "Setup failed at the last step. Cancelling remaining steps. 🛑"
        log_info "Please check the logs above to identify and fix the issue."
        echo -e "${RED}${BOLD}!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!${NC}\n"
    fi
}
trap cleanup_on_error EXIT

# --- Logging Functions ---
log_info() {
    echo -e "${BLUE}[INFO] ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}[SUCCESS] ✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}[WARNING] ⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}[ERROR] ❌ $1${NC}"
}

log_section() {
    echo -e "\n${BOLD}${MAGENTA}==============================================================================${NC}"
    echo -e "${BOLD}${MAGENTA} $1 $2${NC}"
    echo -e "${BOLD}${MAGENTA}==============================================================================${NC}\n"
}

# --- Tool Check ---
check_tools() {
    log_section "STEP 1" "Dependency Check 🛠️"
    log_info "Checking for required tools..."
    local tools=("gcloud" "terraform" "docker" "helm" "kubectl" "grep" "xargs")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "$tool is not installed. Please install it before running this script."
            exit 1
        fi
    done
    log_success "All required tools are present! ✅"
}

# --- Load Environment Variables ---
load_env() {
    log_section "STEP 2" "Loading Environment Variables 📝"
    if [ ! -f "infra/.env" ]; then
        log_error "infra/.env file not found. Please create it first as described in docs/setup.md."
        exit 1
    fi
    # shellcheck disable=SC2046
    export $(grep -v '^#' infra/.env | xargs)
    
    if [ -z "$PROJECT_ID" ]; then
        log_error "PROJECT_ID is not set in infra/.env"
        exit 1
    fi

    log_success "Environment variables loaded for project: $PROJECT_ID 🌟"
}

# --- Auth Check ---
check_auth() {
    log_section "STEP 3" "GCP Authentication Check 🔐"
    log_info "Checking if you are authenticated with gcloud..."
    
    ACTIVE_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -n 1)
    
    if [ -z "$ACTIVE_ACCOUNT" ]; then
        log_error "No active GCP account found. Please run 'gcloud auth login' first."
        exit 1
    fi
    log_success "Authenticated as: $ACTIVE_ACCOUNT 👤"

    log_info "Checking Application Default Credentials (ADC) for Terraform..."
    if ! gcloud auth application-default print-access-token &> /dev/null; then
        log_error "ADC not found or expired. Please run 'gcloud auth application-default login' first. 🗝️"
        exit 1
    else
        log_success "Application Default Credentials ready. ✅"
    fi
}

# --- Project Check ---
check_project() {
    log_section "STEP 4" "GCP Project Validation 🏗️"
    log_info "Checking if project $PROJECT_ID exists and is accessible..."
    if ! gcloud projects describe "$PROJECT_ID" &> /dev/null; then
        log_error "Project $PROJECT_ID not found or you lack permissions. Please create it first. ❌"
        exit 1
    fi
    log_success "Project $PROJECT_ID exists and is accessible. ✅"
    
    log_info "Ensuring gcloud is configured to use $PROJECT_ID..."
    gcloud config set project "$PROJECT_ID" --quiet
}

# --- Billing Check ---
check_billing() {
    log_section "STEP 5" "GCP Billing Validation 💳"
    log_info "Checking billing status for project $PROJECT_ID..."
    BILLING_ENABLED=$(gcloud billing projects describe "$PROJECT_ID" --format="value(billingEnabled)")
    if [ "$BILLING_ENABLED" != "True" ]; then
        log_error "Billing is not enabled for project $PROJECT_ID. Please link a billing account first. ❌"
        exit 1
    fi
    
    if [ ! -z "$BILLING_ACCOUNT_ID" ]; then
        log_info "Verifying if project is linked to $BILLING_ACCOUNT_ID..."
        CURRENT_LINKED_ACCOUNT=$(gcloud billing projects describe "$PROJECT_ID" --format="value(billingAccountName)" | cut -d'/' -f2)
        if [ "$CURRENT_LINKED_ACCOUNT" != "$BILLING_ACCOUNT_ID" ]; then
            log_warning "Project is linked to a different billing account ($CURRENT_LINKED_ACCOUNT) than specified in .env ($BILLING_ACCOUNT_ID)."
        else
            log_success "Project is correctly linked to billing account $BILLING_ACCOUNT_ID. ✅"
        fi
    fi
    log_success "Billing is active for project $PROJECT_ID. ✅"
}

# --- Main Execution ---

log_section "STARTING SETUP" "🚀 Breweries-Case Project Automation 🚀"

# Step 1: Dependency Check
check_tools

# Step 2: Load Environment
load_env

# Step 3: Auth Check
check_auth

# Step 4: Project Validation
check_project

# Step 5: Billing Validation
check_billing

# Step 6: Enable APIs
log_section "STEP 6" "Enabling GCP APIs 🔌"
APIS=(
    "artifactregistry.googleapis.com"
    "compute.googleapis.com"
    "storage.googleapis.com"
    "container.googleapis.com"
)
for api in "${APIS[@]}"; do
    log_info "Enabling $api..."
    gcloud services enable "$api" --project="$PROJECT_ID"
done
log_success "All required APIs enabled! ✨"

# Step 7: Init and Auth Components
log_section "STEP 7" "GCP Components & Auth 🔐"
log_info "Installing gke-gcloud-auth-plugin..."
gcloud components install gke-gcloud-auth-plugin --quiet
log_info "Updating gcloud components..."
gcloud components update --quiet
log_success "GCP components ready. 📦"

# Step 8: Terraform Provisioning
log_section "STEP 8" "Provisioning Infrastructure with Terraform 🏗️"
log_info "Initializing Terraform..."
terraform -chdir=infra/terraform init
log_info "Applying Terraform plan... (This may take ~15 mins) ⏳"
terraform -chdir=infra/terraform apply --auto-approve
if [ $? -eq 0 ]; then
    log_success "Infrastructure provisioned successfully! 🏛️"
else
    log_error "Terraform apply failed. Check the logs above. ❌"
    exit 1
fi

# Step 9: Docker Auth
log_section "STEP 9" "Configuring Docker Auth 🐳"
gcloud auth configure-docker us-central1-docker.pkg.dev --quiet
log_success "Docker authenticated with Artifact Registry. ✅"

# Step 10: Build and Push Docker Images
log_section "STEP 10" "Building and Pushing Docker Images 🚢"
IMAGES=(
    "silver/bees-etl-silver-job:latest src/pipeline/silver/"
    "gold/bees-etl-gold-job:latest src/pipeline/gold/"
    "tests/bees-test-data-quality:latest src/pipeline/tests/"
)

for img_info in "${IMAGES[@]}"; do
    read -r tag path <<< "$img_info"
    log_info "Building $tag from $path..."
    docker buildx build --platform linux/amd64 \
        -t "us-central1-docker.pkg.dev/$PROJECT_ID/bees-docker-repo/$tag" \
        --push "$path"
done

# Build and Push Airflow Image
log_info "Building airflow image from ./infra/kubernetes/airflow/airflow-image/ ..."
docker buildx build --platform linux/amd64 \
    -t "us-central1-docker.pkg.dev/$PROJECT_ID/bees-docker-repo/airflow-image:latest" \
    --push "./infra/kubernetes/airflow/airflow-image/"
log_success "All Docker images pushed to registry. 📤"

# Step 11: Upload Airflow DAGs
log_section "STEP 11" "Uploading Airflow DAGs 🌬️"
log_info "Uploading to GCS bucket gs://bees-airflow-dags/ ..."
gsutil cp -r ./src/pipeline/ gs://bees-airflow-dags/
log_success "DAGs uploaded and project ID injected. 🎯"

# Step 12: GKE Credentials
log_section "STEP 12" "Configuring GKE Context ☸️"
gcloud container clusters get-credentials airflow-cluster --zone us-central1-c --project "$PROJECT_ID"
log_success "GKE context configured. 🔗"

# Step 13: Kubernetes Secrets & RBAC
log_section "STEP 13" "Applying K8s Secrets and RBAC 🛡️"
kubectl create namespace airflow --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f infra/kubernetes/airflow/manifests/rbac.yaml
log_success "Kubernetes configuration applied. 🛡️"

# Step 14: Storage Permissions
log_section "STEP 14" "Setting GCS Permissions 🪣"
BUCKETS=("bees-airflow-logs" "bees-airflow-dags" "bees-storage")
for bucket in "${BUCKETS[@]}"; do
    log_info "Granting storage.objectAdmin on gs://$bucket ..."
    gcloud storage buckets add-iam-policy-binding "gs://$bucket" \
        --member="serviceAccount:gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/storage.objectAdmin" --quiet
done
log_success "Storage permissions granted. 🔓"

# Step 15: Workload Identity (Airflow)
log_section "STEP 15" "Configuring Workload Identity for Airflow 🆔"
gcloud iam service-accounts add-iam-policy-binding \
  "gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[airflow/airflow-service-account]" --quiet

kubectl annotate serviceaccount \
  airflow-service-account \
  --namespace airflow \
  iam.gke.io/gcp-service-account="gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --overwrite
log_success "Airflow Workload Identity configured. ✅"

# Step 16: Persistent Volumes
log_section "STEP 16" "Configuring Persistent Volumes 📂"
kubectl apply -f infra/kubernetes/airflow/manifests/pv-gcs-fuse-dags.yaml
kubectl apply -f infra/kubernetes/airflow/manifests/pvc-gcs-fuse-dags.yaml
kubectl apply -f infra/kubernetes/airflow/manifests/pv-gcs-fuse-logs.yaml
kubectl apply -f infra/kubernetes/airflow/manifests/pvc-gcs-fuse-logs.yaml
log_success "PVCs and PVs applied. 💾"

# Step 17: Install PostgreSQL
log_section "STEP 17" "Installing PostgreSQL 📚"
POSTGRES_PASSWORD="$(LC_ALL=C tr -dc 'A-Za-z0-9' </dev/urandom | head -c 16)"

kubectl -n airflow create secret generic postgresql-secret \
  --from-literal=username="admin" \
  --from-literal=password="$POSTGRES_PASSWORD"

kubectl apply -f infra/kubernetes/postgresql/postgresql.yaml
log_success "PostgreSQL installed. 📚"

# Step 18: Install Airflow with Helm
log_section "STEP 18" "Deploying Airflow via Helm 🎡"
helm repo add apache-airflow https://airflow.apache.org/ --force-update
log_info "Installing/Upgrading Airflow... (This may take ~10 mins) ⏳"
helm upgrade --install airflow apache-airflow/airflow \
  --version 1.16.0 \
  -f infra/kubernetes/airflow/manifests/values_helm.yaml \
  --namespace airflow \
  --set images.airflow.repository="us-central1-docker.pkg.dev/$PROJECT_ID/bees-docker-repo/airflow-image" \
  --set images.airflow.tag="latest" \
  --set images.airflow.pullPolicy="Always" \
  --set data.metadataConnection.pass="$POSTGRES_PASSWORD" \
  --debug
log_success "Airflow deployment initiated. 🚀"

# Step 19: Add Airflow K8s Connection
log_section "STEP 19" "Adding Airflow K8s Connection 🔌"
log_info "Waiting for webserver pod to be ready..."
# Simple wait loop
for i in {1..30}; do
    WEB_POD=$(kubectl get pod -n airflow -l "component=webserver" -o jsonpath="{.items[0].metadata.name}" 2>/dev/null)
    if [ ! -z "$WEB_POD" ]; then
        STATUS=$(kubectl get pod -n airflow "$WEB_POD" -o jsonpath="{.status.phase}")
        if [ "$STATUS" == "Running" ]; then
            break
        fi
    fi
    log_info "Waiting... ($i/30)"
    sleep 10
done

kubectl exec -it "$WEB_POD" -n airflow -- \
    airflow connections add in_cluster_configuration_kubernetes_cluster \
    --conn-type kubernetes \
    --conn-extra '{"in_cluster": true}'
log_success "Airflow Kubernetes connection added. ✅"

# Step 20: Spark Operator
log_section "STEP 20" "Deploying Spark Operator ⚡"
kubectl create namespace spark --dry-run=client -o yaml | kubectl apply -f -
kubectl apply -f infra/kubernetes/spark-operator/rbac.yaml
helm repo add spark-operator https://kubeflow.github.io/spark-operator --force-update
helm upgrade --install spark-operator spark-operator/spark-operator \
  --wait \
  -f infra/kubernetes/spark-operator/values_helm.yaml \
  --namespace spark
log_success "Spark Operator deployed. ⚡"

# Step 21: Workload Identity (Spark)
log_section "STEP 21" "Configuring Workload Identity for Spark 🆔"
gcloud iam service-accounts add-iam-policy-binding \
  "gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.workloadIdentityUser" \
  --member="serviceAccount:$PROJECT_ID.svc.id.goog[spark/spark-service-account]" --quiet

kubectl annotate serviceaccount \
  spark-service-account \
  --namespace spark \
  iam.gke.io/gcp-service-account="gke-service-account@$PROJECT_ID.iam.gserviceaccount.com" \
  --overwrite
log_success "Spark Workload Identity configured. ✅"

log_section "FINISH" "Project Setup Complete! 🎉🌈✨"
log_info "You can now run 'kubectl port-forward svc/airflow-webserver 8080:8080 --namespace airflow' and access http://localhost:8080"
log_info "Happy Data Engineering! 🍻"
