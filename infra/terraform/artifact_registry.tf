resource "google_artifact_registry_repository" "docker_repo" {
  provider      = google
  location      = var.region
  repository_id = var.artifact_registry_name
  description   = "Docker repo for storing pipeline images"
  format        = "DOCKER"

  docker_config {
    immutable_tags = false
  }

}