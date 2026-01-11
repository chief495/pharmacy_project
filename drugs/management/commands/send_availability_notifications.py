from django.core.management.base import BaseCommand
from drugs.views import send_availability_notifications


class Command(BaseCommand):
    help = 'Отправляет email уведомления о наличии препаратов подписанным пользователям'

    def add_arguments(self, parser):
        parser.add_argument(
            '--drug-id',
            type=int,
            help='ID препарата для отправки уведомлений (необязательно)',
        )

    def handle(self, *args, **options):
        drug_id = options.get('drug_id')
        
        self.stdout.write('Начинаю отправку уведомлений о наличии препаратов...')
        
        try:
            notifications_sent = send_availability_notifications(drug_id=drug_id)
            self.stdout.write(
                self.style.SUCCESS(
                    f'Успешно отправлено {notifications_sent} уведомлений.'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Ошибка при отправке уведомлений: {e}')
            )
