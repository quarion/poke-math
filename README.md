# Introduction

Math and Pokemon!
Side project made with Cursor and Sonnet 3.7, with slight manual editing

# Infrastructure:

Initial infrastructure needs to be provisioned manually.
After that, the infrastructure will be managed automatically by CI/CD (eventually).

1. Create GCP project
2. Enable services required by terraform:
    - Bucket for terraform state - `TODO`
    - Google run api - `gcloud services enable run.googleapis.com --project=pokemath-451818`
3. Run initial terrraform
    In infrastructure folder:
    - Create backend.hcl file - TODO: document variables
    - Create terraform.tfvars file - TODO: document variables
    - Run `terraform init "-backend-config=backend.hcl"`
    - Run `terraform plan`
    - Run `terraform apply`
4. Create Cloud Build trigger in the portal
5. Set up firebase:
   - Download the service key to firebase-credentials.json
# Impl plan:
- Add more pokemon images