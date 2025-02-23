terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 4.51"
    }
  }
  backend "gcs" {
    bucket = var.tfstate_bucket
    prefix = "terraform/state"
  }
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
    "secretmanager.googleapis.com"
  ])
  service = each.key
}

# Artifact Registry for Docker images
resource "google_artifact_registry_repository" "poke-math" {
  depends_on  = [google_project_service.apis]
  location    = var.region
  repository_id = "poke-math"
  format      = "DOCKER"
}

# Cloud Run Service
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
      }
    }
  }

  traffic {
    percent         = 100
    latest_revision = true
  }
}

# Firestore Database
resource "google_app_engine_application" "app" {
  location_id = var.region
  database_type = "CLOUD_FIRESTORE"
}

# Cloud Build Trigger
resource "google_cloudbuild_trigger" "app-deploy" {
  name = "poke-math-deploy-trigger"
  filename = "cloudbuild.yaml"
  github {
    owner = "quarion"
    name  = "poke-math"
    push {
      branch = "main"
    }
  }
}

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
