resource "google_container_node_pool" "main_pool" {
  name       = "main-pool"
  cluster    = google_container_cluster.gke.name
  location   = var.zone

  node_config {
    machine_type    = "c2d-highcpu-8"
    disk_size_gb    = 100
    image_type      = "COS_CONTAINERD"
    disk_type       = "pd-balanced"
    spot            = true
    service_account = google_service_account.gke_sa.email

    metadata = {
      disable-legacy-endpoints = "true"
    }

    shielded_instance_config {
      enable_integrity_monitoring = true
    }
  }

  autoscaling {
    min_node_count = 1
    max_node_count = 5
  }

  management {
    auto_repair  = true
    auto_upgrade = true
  }

  upgrade_settings {
    max_surge       = 1
    max_unavailable = 0
  }

  placement_policy {
    type = "COMPACT"
  }
}