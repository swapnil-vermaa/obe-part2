from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0006_course_department'),
    ]

    operations = [
        migrations.AddField(
            model_name='course',
            name='is_lab',
            field=models.BooleanField(
                default=False,
                help_text='Lab course offering (separate list; different Students & Marks sub-tabs).',
            ),
        ),
    ]
