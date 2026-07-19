project_id         = "pokemath-451818"
project_number     = "991216996410"
billing_account_id = "014916-57FD71-27BFF9"
region             = "europe-west1"

terraform_state_bucket = "tfstate-pokemath-europe-prod"
terraform_state_operators = [
  "user:quarion.pl@gmail.com",
]

custom_domain     = "pokemath.quarion.dev"
github_owner      = "quarion"
github_repository = "poke-math"

# This is the release switch. Change it only after the private verification
# checklist passes and the owner explicitly approves public exposure.
public_access_enabled = true
