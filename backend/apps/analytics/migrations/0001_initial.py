from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("lectures", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="SessionAnalytics",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("total_questions", models.IntegerField(default=0)),
                ("evaluated_responses", models.IntegerField(default=0)),
                ("average_accuracy", models.FloatField(blank=True, null=True)),
                ("average_completeness", models.FloatField(blank=True, null=True)),
                ("average_clarity", models.FloatField(blank=True, null=True)),
                ("overall_effectiveness", models.FloatField(blank=True, null=True)),
                ("summary_confidence", models.FloatField(blank=True, null=True)),
                ("engagement_score", models.FloatField(blank=True, null=True)),
                ("insights", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "session",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analytics",
                        to="lectures.session",
                    ),
                ),
            ],
            options={
                "ordering": ["-updated_at"],
            },
        ),
    ]
