resource "google_secret_manager_secret" "flask_secret_key" {
  depends_on = [google_project_service.apis]

  project             = var.project_id
  secret_id           = "poke-math-flask-secret-key"
  deletion_protection = true

  replication {
    auto {}
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_secret_manager_secret_iam_member" "runtime_secret_accessor" {
  project   = var.project_id
  secret_id = google_secret_manager_secret.flask_secret_key.secret_id
  role      = "roles/secretmanager.secretAccessor"
  member    = local.runtime_service_account
}

resource "google_cloud_run_v2_service" "app" {
  depends_on = [
    google_project_service.apis,
    google_secret_manager_secret_iam_member.runtime_secret_accessor,
  ]

  project             = var.project_id
  name                = "poke-math"
  location            = var.region
  ingress             = "INGRESS_TRAFFIC_ALL"
  deletion_protection = true

  template {
    service_account                  = google_service_account.runtime.email
    timeout                          = "300s"
    max_instance_request_concurrency = 80

    scaling {
      min_instance_count = 0
      max_instance_count = 1
    }

    containers {
      name  = "poke-math"
      image = "${var.region}-docker.pkg.dev/${var.project_id}/poke-math/poke-math:latest"

      ports {
        name           = "http1"
        container_port = 8080
      }

      env {
        name  = "APP_ENVIRONMENT"
        value = "production"
      }

      env {
        name = "FLASK_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.flask_secret_key.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
        cpu_idle = true
      }

      startup_probe {
        failure_threshold     = 1
        initial_delay_seconds = 0
        period_seconds        = 240
        timeout_seconds       = 240

        tcp_socket {
          port = 8080
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  lifecycle {
    # Cloud Build owns immutable image promotion. Terraform owns everything
    # else about the service and deliberately ignores only image changes.
    ignore_changes = [
      client,
      client_version,
      template[0].containers[0].image,
    ]
  }
}

resource "google_cloud_run_v2_service_iam_member" "public" {
  for_each = var.public_access_enabled ? toset(["allUsers"]) : toset([])

  project  = var.project_id
  location = google_cloud_run_v2_service.app.location
  name     = google_cloud_run_v2_service.app.name
  role     = "roles/run.invoker"
  member   = each.value
}

# This block incorporates the previously local-only domain mapping and makes it
# reproducible. Domain ownership verification and DNS remain documented gates.
resource "google_cloud_run_domain_mapping" "default" {
  project  = var.project_id
  name     = var.custom_domain
  location = google_cloud_run_v2_service.app.location

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.app.name
  }
}
