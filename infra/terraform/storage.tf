resource "google_storage_bucket" "bees_storage" {
    name     = var.bucket_storage_name
    location = var.region
    force_destroy = true
}


resource "google_storage_bucket" "airflow_logs" {
    name     = var.bucket_logs_name
    location = var.region
    force_destroy = true
}

resource "google_storage_bucket" "airflow_dags" {
    name     = var.bucket_dags_name
    location = var.region
    force_destroy = true
}