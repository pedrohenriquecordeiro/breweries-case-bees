output "cluster_name" {
  value = google_container_cluster.gke.name
}

output "cluster_endpoint" {
  value = google_container_cluster.gke.endpoint
}

output "service_account_email" {
  value = google_service_account.gke_sa.email
}

output "bucket_storage_name" {
  value = google_storage_bucket.bees_storage.name
}

output "bucket_logs_name" {
  value = google_storage_bucket.airflow_logs.name
}

output "bucket_dags_name" {
  value = google_storage_bucket.airflow_dags.name
}