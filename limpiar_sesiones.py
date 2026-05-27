from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from django.utils import timezone

class Command(BaseCommand):
    help = 'Limpia sesiones expiradas'

    def handle(self, *args, **options):
        expiradas = Session.objects.filter(expire_date__lt=timezone.now())
        count = expiradas.count()
        expiradas.delete()
        self.stdout.write(self.style.SUCCESS(f'Se eliminaron {count} sesiones expiradas'))
