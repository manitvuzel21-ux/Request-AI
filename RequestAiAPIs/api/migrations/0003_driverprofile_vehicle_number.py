from django.db import migrations, models


def assign_vehicle_numbers(apps, schema_editor):
    DriverProfile = apps.get_model('api', 'DriverProfile')
    for profile in DriverProfile.objects.filter(vehicle_number__isnull=True).iterator():
        profile.vehicle_number = f'UNASSIGNED-{profile.pk}'
        profile.save(update_fields=['vehicle_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_driverprofile_ride_driver'),
    ]

    operations = [
        migrations.AddField(
            model_name='driverprofile',
            name='vehicle_number',
            field=models.CharField(max_length=20, null=True, unique=True),
        ),
        migrations.RunPython(assign_vehicle_numbers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='driverprofile',
            name='vehicle_number',
            field=models.CharField(max_length=20, unique=True),
        ),
    ]
