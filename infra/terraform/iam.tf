resource "google_service_account" "gke_sa" {
  account_id   = "gke-service-account"
  display_name = "GKE Compute Engine SA"
}

resource "google_project_iam_member" "gke_sa_roles" {
  for_each = toset([
    "roles/container.admin",
    "roles/compute.networkAdmin",
    "roles/iam.serviceAccountUser",
    "roles/monitoring.viewer",
    "roles/logging.logWriter",
    "roles/storage.admin",
    "roles/artifactregistry.admin",
    "roles/artifactregistry.reader"
  ])
  project = var.project_id
  role    = each.key
  member  = "serviceAccount:${google_service_account.gke_sa.email}"
}