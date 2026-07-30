from collections import defaultdict
from datetime import timedelta
from datetime import date as date_class

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.lectures.models import Session


class Command(BaseCommand):
    help = "List likely stale or duplicate test sessions without modifying data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--date",
            default=None,
            help="Optional YYYY-MM-DD date to audit; defaults to today in the current timezone.",
        )
        parser.add_argument(
            "--window-seconds",
            type=int,
            default=15,
            help="Flag sessions with the same title and lecturer created within this many seconds.",
        )

    def handle(self, *args, **options):
        target_date = (
            date_class.fromisoformat(options["date"])
            if options["date"]
            else timezone.localdate()
        )
        window = timedelta(seconds=options["window_seconds"])

        sessions = list(
            Session.objects.filter(created_at__date=target_date).order_by("created_at")
        )

        self.stdout.write(f"Sessions created on {target_date.isoformat()}: {len(sessions)}")
        for session in sessions:
            self.stdout.write(
                f"id={session.id} title={session.title!r} lecturer_id={session.lecturer_id} created_at={session.created_at.isoformat()}"
            )

        self.stdout.write("")
        self.stdout.write(
            f"Potential duplicates (same normalized title + lecturer_id within {options['window_seconds']} seconds):"
        )

        grouped = defaultdict(list)
        for session in sessions:
            key = (session.title.strip().lower(), session.lecturer_id)
            grouped[key].append(session)

        found = False
        for (title, lecturer_id), items in grouped.items():
            items = sorted(items, key=lambda item: item.created_at)
            for previous, current in zip(items, items[1:]):
                delta = current.created_at - previous.created_at
                if delta <= window:
                    found = True
                    self.stdout.write(
                        f"title={title!r} lecturer_id={lecturer_id} previous_id={previous.id} previous_created_at={previous.created_at.isoformat()} current_id={current.id} current_created_at={current.created_at.isoformat()} delta_seconds={delta.total_seconds():.1f}"
                    )

        if not found:
            self.stdout.write("No likely duplicates found.")