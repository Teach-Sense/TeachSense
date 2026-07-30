from django.core.management.base import BaseCommand

from apps.lecturers.models import Lecturer
from apps.users.models import User


class Command(BaseCommand):
    help = "Create missing Lecturer profiles for users whose role is lecturer."

    def handle(self, *args, **options):
        created_count = 0
        scanned_count = 0

        for user in User.objects.filter(role="lecturer").iterator():
            scanned_count += 1
            _, created = Lecturer.objects.get_or_create(user=user)
            if created:
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Scanned {scanned_count} lecturer users and created {created_count} missing lecturer profiles."
            )
        )