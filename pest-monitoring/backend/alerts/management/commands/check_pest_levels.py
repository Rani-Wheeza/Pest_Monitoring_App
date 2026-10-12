from django.conf import settings
from django.core.management.base import BaseCommand

from alerts.services import run_threshold_check


class Command(BaseCommand):
    help = "Check pest activity against the thresholds and send alerts (run hourly by an AKS CronJob)."

    def add_arguments(self, parser):
        parser.add_argument("--threshold", type=int, default=settings.ALERT_THRESHOLD,
                            help="Sightings in 30 days that count as high activity.")

    def handle(self, *args, threshold, **options):
        result = run_threshold_check(threshold)
        for line in result.details:
            self.stdout.write(f"  {line}")
        self.stdout.write(self.style.SUCCESS(
            f"Alerts created: {result.alerts_created}, updated: {result.alerts_updated}, "
            f"notifications sent: {result.notifications_sent}, failed: {result.notifications_failed}"))
