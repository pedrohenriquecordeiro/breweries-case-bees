resource "google_container_cluster" "gke" {
  name     = var.cluster_name
  location = var.zone

  deletion_protection = false

  release_channel {
    channel = "REGULAR"
  }

  network    = google_compute_network.vpc.name
  subnetwork = google_compute_subnetwork.subnet.name

  remove_default_node_pool = true
  initial_node_count       = 1 # Required when removing default pool

  ip_allocation_policy {
    cluster_secondary_range_name  = "pods"
    services_secondary_range_name = "services"
  }

  logging_config {
    enable_components = ["SYSTEM_COMPONENTS", "WORKLOADS"]
  }

  monitoring_config {
    enable_components = [
      "SYSTEM_COMPONENTS",
      "STORAGE",
      "POD",
      "DEPLOYMENT",
      "STATEFULSET",
      "DAEMONSET",
      "HPA",
      "JOBSET",
      "CADVISOR",
      "KUBELET",
      "DCGM"
    ]
    managed_prometheus {
      enabled = true
    }
  }

  vertical_pod_autoscaling {
    enabled = true
  }

  addons_config {
    http_load_balancing {
      disabled = false
    }
    horizontal_pod_autoscaling {
      disabled = true
    }
    gce_persistent_disk_csi_driver_config {
      enabled = true
    }
    gcs_fuse_csi_driver_config {
      enabled = true
    }
    dns_cache_config {
      enabled = true
    }
  }

  workload_identity_config {
    workload_pool = "${var.project_id}.svc.id.goog"
  }

  lifecycle {
    ignore_changes = [node_config] # Safe for auto-upgrade-related changes
  }
}