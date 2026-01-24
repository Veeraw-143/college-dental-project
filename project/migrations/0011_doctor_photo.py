# Generated migration for Doctor photo field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('project', '0010_doctor_availability_days'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='photo',
            field=models.ImageField(blank=True, help_text='Doctor profile photo', null=True, upload_to='doctors/'),
        ),
    ]
