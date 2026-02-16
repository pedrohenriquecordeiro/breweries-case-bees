variable "project_id" {
  description = "GCP Project ID"
  type        = string
}

variable "region" {
  description = "GCP Region"
  type        = string
  default     = "us-central1"
}

variable "zone" {
  description = "GCP Location"
  type        = string
  default     = "us-central1-c"
}

variable "cluster_name" {
  description = "Name of the GKE cluster"
  type        = string
  default     = "airflow-cluster"
}

variable "bucket_storage_name" {
  description = "Name of the GCS bucket for storage"
  type        = string
  default     = "bees-storage"
}

variable "bucket_logs_name" {
  description = "Name of the GCS bucket for logs"
  type        = string
  default     = "bees-airflow-logs"
}

variable "bucket_dags_name" {
  description = "Name of the GCS bucket for DAGs"
  type        = string
  default     = "bees-airflow-dags"
}

variable "artifact_registry_name" {
  description = "Name of the Artifact Registry repository"
  type        = string
  default     = "bees-docker-repo"
} 
