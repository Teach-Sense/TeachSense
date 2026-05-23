# Generated migration for Device model

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Device',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('device_id', models.CharField(help_text='Unique device identifier (MAC address or serial number)', max_length=255, unique=True)),
                ('device_name', models.CharField(help_text='Human-friendly device name', max_length=255)),
                ('device_type', models.CharField(choices=[('tablet', 'Tablet'), ('laptop', 'Laptop'), ('desktop', 'Desktop'), ('smartboard', 'Smart Board'), ('speaker', 'Speaker System'), ('other', 'Other')], default='tablet', max_length=20)),
                ('location', models.CharField(blank=True, help_text='Physical location (e.g., Building A, Room 101)', max_length=255)),
                ('device_token', models.CharField(help_text='Authentication token for device-to-server communication', max_length=255, unique=True)),
                ('os_type', models.CharField(blank=True, help_text='Operating system (iOS, Android, Linux, Windows)', max_length=50)),
                ('os_version', models.CharField(blank=True, max_length=50)),
                ('app_version', models.CharField(blank=True, max_length=50)),
                ('status', models.CharField(choices=[('online', 'Online'), ('offline', 'Offline'), ('inactive', 'Inactive'), ('maintenance', 'Maintenance')], default='offline', max_length=20)),
                ('last_sync', models.DateTimeField(blank=True, null=True)),
                ('last_sync_status', models.CharField(blank=True, help_text='Status message from last sync', max_length=255)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'Device',
                'verbose_name_plural': 'Devices',
                'ordering': ['-last_sync'],
            },
        ),
        migrations.CreateModel(
            name='DeviceSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sync_type', models.CharField(choices=[('pull', 'Pull data from cloud'), ('push', 'Push data to cloud'), ('bidirectional', 'Bidirectional sync')], max_length=20)),
                ('status', models.CharField(choices=[('success', 'Success'), ('partial', 'Partial sync'), ('failed', 'Failed')], max_length=20)),
                ('items_pulled', models.IntegerField(default=0)),
                ('items_pushed', models.IntegerField(default=0)),
                ('sync_duration_ms', models.IntegerField(default=0, help_text='Duration of sync in milliseconds')),
                ('error_message', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('device', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sync_logs', to='devices.device')),
            ],
            options={
                'verbose_name': 'Device Sync Log',
                'verbose_name_plural': 'Device Sync Logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
