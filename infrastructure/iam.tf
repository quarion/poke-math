resource "google_service_account" "runtime" {
  depends_on = [google_project_service.apis]

  project      = var.project_id
  account_id   = "poke-math-service"
  display_name = "PokeMath Cloud Run runtime"
  description  = "Runtime identity; reads and writes player data in Firestore"
}

resource "google_project_iam_member" "runtime_firestore_user" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = local.runtime_service_account
}

resource "google_service_account" "build" {
  depends_on = [google_project_service.apis]

  project      = var.project_id
  account_id   = "poke-math-build"
  display_name = "PokeMath Cloud Build deployer"
  description  = "Builds the application image and deploys it to Cloud Run"

  lifecycle {
    prevent_destroy = true
  }
}

resource "google_project_iam_member" "build_project_roles" {
  for_each = toset([
    "roles/artifactregistry.writer",
    "roles/logging.logWriter",
    "roles/run.developer",
  ])

  project = var.project_id
  role    = each.value
  member  = local.build_service_account
}

resource "google_service_account_iam_member" "build_uses_runtime" {
  service_account_id = google_service_account.runtime.name
  role               = "roles/iam.serviceAccountUser"
  member             = local.build_service_account
}

resource "google_storage_bucket_iam_member" "build_reads_source" {
  bucket = "${var.project_id}_cloudbuild"
  role   = "roles/storage.objectViewer"
  member = local.build_service_account
}
