terraform {
  required_version = ">= 1.10, < 2.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.40"
    }
  }

  backend "gcs" {}
}

provider "google" {
  project               = var.project_id
  region                = var.region
  billing_project       = var.project_id
  user_project_override = true
}

locals {
  runtime_service_account = "serviceAccount:${google_service_account.runtime.email}"
  build_service_account   = "serviceAccount:${google_service_account.build.email}"
}

resource "google_project_service" "apis" {
  for_each = toset([
    "artifactregistry.googleapis.com",
    "billingbudgets.googleapis.com",
    "cloudbuild.googleapis.com",
    "cloudresourcemanager.googleapis.com",
    "firebase.googleapis.com",
    "firestore.googleapis.com",
    "iam.googleapis.com",
    "identitytoolkit.googleapis.com",
    "monitoring.googleapis.com",
    "run.googleapis.com",
    "secretmanager.googleapis.com",
  ])

  project            = var.project_id
  service            = each.key
  disable_on_destroy = false
}

resource "google_artifact_registry_repository" "app" {
  depends_on = [google_project_service.apis]

  project       = var.project_id
  location      = var.region
  repository_id = "poke-math"
  description   = "PokeMath deployable container images"
  format        = "DOCKER"

  # Keep the active deployment and one rollback image; delete older,
  # rebuildable versions after the retention window.
  cleanup_policy_dry_run = false

  cleanup_policies {
    id     = "keep-recent-deployments"
    action = "KEEP"

    most_recent_versions {
      package_name_prefixes = ["poke-math"]
      keep_count            = 2
    }
  }

  cleanup_policies {
    id     = "delete-old-untagged"
    action = "DELETE"

    condition {
      tag_state  = "ANY"
      older_than = "604800s"
    }
  }

  lifecycle {
    prevent_destroy = true
  }
}
