# Generated manually to add student enrollment tracking to sessions.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("lectures", "0001_initial"),
        ("users", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="enrolled_students",
            field=models.ManyToManyField(
                blank=True,
                help_text="Students enrolled in this session",
                related_name="sessions",
                related_query_name="session",
                to="users.user",
            ),
        ),
    ]