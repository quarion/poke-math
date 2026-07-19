output "service_url" {
  value       = google_cloud_run_v2_service.app.uri
  description = "Generated Cloud Run URL"
}

output "custom_url" {
  value       = "https://${var.custom_domain}"
  description = "Public custom URL after the explicit release gate is enabled"
}

output "runtime_service_account" {
  value       = google_service_account.runtime.email
  description = "Least-privilege runtime identity"
}

output "build_service_account" {
  value       = google_service_account.build.email
  description = "Least-privilege build and deploy identity"
}
