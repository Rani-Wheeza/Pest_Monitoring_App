from django.core.management.base import BaseCommand

from reference.seed import seed_reference_data


class Command(BaseCommand):
    help = "Add the starter districts, pest species and tags (safe to run more than once)."

    def handle(self, *args, **options):
        created = seed_reference_data()
        self.stdout.write(self.style.SUCCESS(f"Reference data ready: {created}"))
