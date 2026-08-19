"""Signals for lecturer profile maintenance."""

from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from apps.lecturers.models import Lecturer
from apps.users.models import User


@receiver(pre_save, sender=User)
def store_previous_role(sender, instance, **kwargs):
	"""Cache the previous role so role promotions can be detected on save."""
	if not instance.pk:
		instance._previous_role = None
		return

	instance._previous_role = sender.objects.filter(pk=instance.pk).values_list("role", flat=True).first()


@receiver(post_save, sender=User)
def ensure_lecturer_profile(sender, instance, created, **kwargs):
	"""Create a Lecturer profile whenever a user becomes a lecturer."""
	previous_role = getattr(instance, "_previous_role", None)
	should_create_profile = instance.role == "lecturer" and (created or previous_role != "lecturer")

	if should_create_profile:
		Lecturer.objects.get_or_create(user=instance)
