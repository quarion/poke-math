# TODO: Separate definition for CI and prod

terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.51"
    }
  }
  backend "gcs" {}  # Leave empty and configure during initialization
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Enable required APIs
resource "google_project_service" "apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "run.googleapis.com",
    "firestore.googleapis.com",
    "cloudbuild.googleapis.com",
    "secretmanager.googleapis.com",
    "firebase.googleapis.com"
  ])
  service = each.key
  disable_on_destroy = false
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "poke-math" {
  depends_on  = [google_project_service.apis]
  location    = var.region
  repository_id = "poke-math"
  format      = "DOCKER"
}

# Cloud Build Trigger
# Does not work right now, possibly fix later. For now created manually.
# resource "google_cloudbuild_trigger" "app-deploy" {
#   depends_on = [google_project_service.apis]
#   name       = "poke-math-deploy-trigger"
#   filename   = "cloudbuild.yaml"
#   github {
#     owner = "quarion"
#     name  = "poke-math"
#     push {
#       branch = "^main$"  # Use regex pattern for exact match
#     }
#   }
# }

# IAM Roles for Cloud Build
resource "google_project_iam_member" "cloudbuild_deploy" {
  project = var.project_id
  role    = "roles/run.admin"
  member  = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
}

resource "google_project_iam_member" "cloudbuild_sa_user" {
  project = var.project_id
  role    = "roles/iam.serviceAccountUser"
  member  = "serviceAccount:${var.project_number}@cloudbuild.gserviceaccount.com"
}

# Create a dedicated service account for Cloud Run
resource "google_service_account" "cloud_run_service_account" {
  depends_on  = [google_project_service.apis]
  account_id  = "poke-math-service"
  display_name = "Service Account for Poke Math Cloud Run Service"
}

# Grant Firestore permissions to the service account
resource "google_project_iam_member" "firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Grant Firebase Auth permissions
resource "google_project_iam_member" "firebase_auth_admin" {
  project = var.project_id
  role    = "roles/firebaseauth.admin"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Grant Firebase Admin SDK access
resource "google_project_iam_member" "firebase_admin" {
  project = var.project_id
  role    = "roles/firebase.admin"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Additional Firestore specific role for more detailed access control
resource "google_project_iam_member" "firestore_admin" {
  project = var.project_id
  role    = "roles/datastore.owner"
  member  = "serviceAccount:${google_service_account.cloud_run_service_account.email}"
}

# Cloud Run Service
# Note, this fails to apply if there is no image in the registry, so before first run the image needs to be pushed manually.
resource "google_cloud_run_service" "poke-math" {
  name     = "poke-math"
  location = var.region

  template {
    spec {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/poke-math/poke-math:latest"
        env {
          name  = "FLASK_ENV"
          value = "production"
        }
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
      }
      # Use the dedicated service account instead of the default compute service account
      service_account_name = google_service_account.cloud_run_service_account.email
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# IAM policy to make the service public
resource "google_cloud_run_service_iam_member" "public" {
  location = google_cloud_run_service.poke-math.location
  service  = google_cloud_run_service.poke-math.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Firestore Database
resource "google_app_engine_application" "app" {
  location_id = "europe-west"
  database_type = "CLOUD_FIRESTORE"
}
