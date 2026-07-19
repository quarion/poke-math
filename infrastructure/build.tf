resource "google_cloudbuild_trigger" "main" {
  depends_on = [
    google_project_iam_member.build_project_roles,
    google_service_account_iam_member.build_uses_runtime,
  ]

  project         = var.project_id
  location        = "global"
  name            = "main"
  description     = "Build and privately deploy PokeMath from the main branch"
  filename        = "cloudbuild.yaml"
  service_account = google_service_account.build.id

  github {
    owner = var.github_owner
    name  = var.github_repository

    push {
      branch = "^main$"
    }
  }

  substitutions = {
    _REGION = var.region
  }
}
