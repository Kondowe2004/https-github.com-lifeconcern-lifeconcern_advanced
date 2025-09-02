from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.core.management import call_command

class Command(BaseCommand):
    help = "Run migrations, load seed data, and create demo superuser admin/admin123"
    def handle(self, *args, **kwargs):
        call_command('migrate', interactive=False)
        try:
            call_command('loaddata', 'fixtures/seed.json')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Seed load warning: {e}"))
        User = get_user_model()
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Created demo superuser admin/admin123'))
        else:
            self.stdout.write('Demo superuser already exists')
        self.stdout.write(self.style.SUCCESS('Bootstrap complete.'))
