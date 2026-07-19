resource "google_billing_budget" "monthly_guardrail" {
  depends_on = [google_project_service.apis]

  billing_account = var.billing_account_id
  display_name    = "PokeMath monthly guardrail"

  amount {
    specified_amount {
      currency_code = "PLN"
      units         = "10"
    }
  }

  budget_filter {
    projects               = ["projects/${var.project_number}"]
    calendar_period        = "MONTH"
    credit_types_treatment = "INCLUDE_ALL_CREDITS"
  }

  threshold_rules {
    threshold_percent = 0.10
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 0.90
    spend_basis       = "CURRENT_SPEND"
  }

  threshold_rules {
    threshold_percent = 1.00
    spend_basis       = "CURRENT_SPEND"
  }

  lifecycle {
    # The console-created email-recipient rule cannot be represented without
    # also configuring Pub/Sub or Monitoring channels in provider 7.40.
    # Preserve it exactly as imported so project-owner email alerts stay on.
    ignore_changes = [all_updates_rule]
  }

}
