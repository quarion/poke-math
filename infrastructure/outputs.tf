output "service_url" {
  value       = google_cloud_run_service.poke-math.status[0].url
  description = "The URL of the deployed Cloud Run service"
}