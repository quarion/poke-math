variable "project_id" {
  description = "Google Cloud project ID"
  type        = string
}

variable "project_number" {
  description = "Google Cloud numeric project identifier"
  type        = string
}

variable "region" {
  description = "Region for Cloud Run, Artifact Registry, and state storage"
  type        = string
  default     = "europe-west1"
}

variable "billing_account_id" {
  description = "Billing account ID without the billingAccounts/ prefix"
  type        = string
}

variable "terraform_state_bucket" {
  description = "Pre-existing GCS bucket used by the Terraform backend"
  type        = string
  default     = "tfstate-pokemath-europe-prod"
}

variable "terraform_state_operators" {
  description = "Principals allowed to read and update Terraform state objects"
  type        = set(string)
  default     = ["user:quarion.pl@gmail.com"]
}

variable "custom_domain" {
  description = "Custom hostname mapped to Cloud Run"
  type        = string
  default     = "pokemath.quarion.dev"
}

variable "github_owner" {
  description = "GitHub owner used by the existing Cloud Build connection"
  type        = string
  default     = "quarion"
}

variable "github_repository" {
  description = "GitHub repository used by the Cloud Build trigger"
  type        = string
  default     = "poke-math"
}

variable "public_access_enabled" {
  description = "Explicit release gate for unauthenticated Cloud Run access"
  type        = bool
  default     = false
}

variable "alert_email" {
  description = "Email address receiving operational usage alerts"
  type        = string
  default     = "quarion.pl@gmail.com"
}
