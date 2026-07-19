resource "google_monitoring_notification_channel" "owner_email" {
  depends_on = [google_project_service.apis]

  project      = var.project_id
  display_name = "PokeMath owner email"
  description  = "Operational usage alerts for PokeMath"
  type         = "email"
  labels = {
    email_address = var.alert_email
  }
}

resource "google_monitoring_alert_policy" "cloud_run_usage" {
  depends_on = [google_project_service.apis]

  project               = var.project_id
  display_name          = "PokeMath unusual Cloud Run usage"
  combiner              = "OR"
  severity              = "WARNING"
  notification_channels = [google_monitoring_notification_channel.owner_email.name]

  conditions {
    display_name = "More than 1,000 requests in 5 minutes"

    condition_threshold {
      filter = join(" AND ", [
        "resource.type = \"cloud_run_revision\"",
        "resource.labels.service_name = \"${google_cloud_run_v2_service.app.name}\"",
        "metric.type = \"run.googleapis.com/request_count\"",
      ])
      comparison      = "COMPARISON_GT"
      threshold_value = 1000
      duration        = "0s"

      aggregations {
        alignment_period     = "300s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  conditions {
    display_name = "More than 5 billable minutes in 15 minutes"

    condition_threshold {
      filter = join(" AND ", [
        "resource.type = \"cloud_run_revision\"",
        "resource.labels.service_name = \"${google_cloud_run_v2_service.app.name}\"",
        "metric.type = \"run.googleapis.com/container/billable_instance_time\"",
      ])
      comparison      = "COMPARISON_GT"
      threshold_value = 300
      duration        = "0s"

      aggregations {
        alignment_period     = "900s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  documentation {
    mime_type = "text/markdown"
    content   = "Traffic or compute is far above PokeMath's normal baseline. Inspect Cloud Run metrics and logs. If abuse is continuing, use the public-access emergency stop in infrastructure/README.md."
  }

  alert_strategy {
    auto_close           = "3600s"
    notification_prompts = ["OPENED", "CLOSED"]
  }
}

resource "google_monitoring_alert_policy" "firestore_usage" {
  depends_on = [google_project_service.apis]

  project               = var.project_id
  display_name          = "PokeMath unusual Firestore usage"
  combiner              = "OR"
  severity              = "WARNING"
  notification_channels = [google_monitoring_notification_channel.owner_email.name]

  conditions {
    display_name = "More than 5,000 document reads in 1 hour"

    condition_threshold {
      filter          = "resource.type = \"firestore_instance\" AND metric.type = \"firestore.googleapis.com/document/read_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 5000
      duration        = "0s"

      aggregations {
        alignment_period     = "3600s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  conditions {
    display_name = "More than 2,000 document writes in 1 hour"

    condition_threshold {
      filter          = "resource.type = \"firestore_instance\" AND metric.type = \"firestore.googleapis.com/document/write_count\""
      comparison      = "COMPARISON_GT"
      threshold_value = 2000
      duration        = "0s"

      aggregations {
        alignment_period     = "3600s"
        per_series_aligner   = "ALIGN_SUM"
        cross_series_reducer = "REDUCE_SUM"
      }
    }
  }

  documentation {
    mime_type = "text/markdown"
    content   = "Firestore operations are far above PokeMath's normal baseline and approaching a meaningful share of the daily free allowance. Inspect Firestore usage and Cloud Run logs; use the emergency stop if abuse is continuing."
  }

  alert_strategy {
    auto_close           = "3600s"
    notification_prompts = ["OPENED", "CLOSED"]
  }
}
