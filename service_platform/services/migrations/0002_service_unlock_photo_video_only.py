from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


def disable_legacy_call_services(apps, schema_editor):
    Service = apps.get_model('services', 'Service')
    Service.objects.filter(service_type__in=['audio_call', 'video_call']).exclude(
        status__in=['rejected', 'disabled']
    ).update(status='disabled')


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='ServiceUnlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('unlocked_at', models.DateTimeField(auto_now_add=True)),
                ('service', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='unlocks', to='services.service')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='service_unlocks', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(
            model_name='serviceunlock',
            constraint=models.UniqueConstraint(fields=('user', 'service'), name='unique_user_service_unlock'),
        ),
        migrations.AlterField(
            model_name='service',
            name='service_type',
            field=models.CharField(
                choices=[('general', 'Photo and Video')],
                default='general',
                max_length=20,
            ),
        ),
        migrations.RunPython(disable_legacy_call_services, migrations.RunPython.noop),
    ]