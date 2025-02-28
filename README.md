# Introduction

Math and Pokemon!
Side project made with Cursor and Sonnet 3.7. Almost 100% of code is AI generated, with very slight manual tweaking

Live version: https://poke-math-991216996410.europe-west1.run.app/

# Infrastructure:

Follow those steps to provision new environment

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
   - Download the firebase sdk config to login.html

# TODO

List of ideas to add in the future

Functional:
- Make sure the log-in will work on mobile
- Improve equations generation to make sure there is a solution
- Add custom domain
- Better progress information. Clear indication of gaining exp after mission, more exp for more difficult options
- Complete pre-defined missions
- Sharing missions
- Allow users to create their own missions

Tech:
- Remove unnecessary comments from code
- Switch to full Firebase log-in flow, including guest account and login/password auth.
- Re-write frontend in React or make it from scratch in Jinja. Understand how to steer Cursor to make nice frontends
- Move completed missions to separate collection
- CI for infra

Other:
- Blog/twitt about experience with Cursor