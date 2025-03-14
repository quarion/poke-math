# Introduction

Math and Pokemon!
Side project made with Cursor and Sonnet 3.7. Almost 100% of the code is AI generated, with very slight manual tweaking

Live version: https://poke-math-991216996410.europe-west1.run.app/

# Infrastructure:

Follow those steps to provision new environment

1. Create GCP project
2. Enable services required by terraform:
   - Bucket for terraform state
   - Google run api - `gcloud services enable run.googleapis.com --project=<project id>`
3. Run initial terrraform
   In infrastructure folder:
   - Create backend.hcl file with variables:
     - bucket = "<bucket name>"
     - prefix = "terraform/state"
   - Create terraform.tfvars file with variables:
     - project_id      = "<project id>"
     - project_number  = "<project number>"
   - Run `terraform init "-backend-config=backend.hcl"`
   - Run `terraform plan`
   - Run `terraform apply`
4. Create Cloud Build trigger in the portal
5. Set up firebase:
   - Download the service key to firebase-credentials.json
   - Download the firebase sdk config to login.html