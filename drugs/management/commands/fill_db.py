from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from drugs.models import (
    Drug, PharmacyNetwork, Pharmacy, Availability, 
    Analogue, UserSubscription, PriceHistory
)
import random
from decimal import Decimal
from datetime import datetime, timedelta

CustomUser = get_user_model()

class Command(BaseCommand):
    help = 'Заполняет базу данных тестовыми данными для Pharmacy Project'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Начинаем заполнение базы данных...'))
        
        # Очищаем старые данные (осторожно!)
        # Drug.objects.all().delete()
        # Pharmacy.objects.all().delete()
        
        # 1. Создаем тестовых пользователей
        self.create_users()
        
        # 2. Создаем препараты
        drugs = self.create_drugs()
        
        # 3. Создаем аналоги
        self.create_analogues(drugs)
        
        # 4. Создаем аптечные сети и аптеки
        pharmacies = self.create_pharmacies()
        
        # 5. Создаем наличие препаратов в аптеках
        self.create_availabilities(drugs, pharmacies)
        
        # 6. Создаем подписки
        self.create_subscriptions(drugs)
        
        self.stdout.write(self.style.SUCCESS('База данных успешно заполнена!'))
    
    def create_users(self):
        """Создание тестовых пользователей"""
        users_data = [
            {'email': 'user1@example.com', 'first_name': 'Иван', 'last_name': 'Петров'},
            {'email': 'user2@example.com', 'first_name': 'Мария', 'last_name': 'Иванова'},
            {'email': 'user3@example.com', 'first_name': 'Алексей', 'last_name': 'Сидоров'},
        ]
        
        for user_data in users_data:
            user, created = CustomUser.objects.get_or_create(
                email=user_data['email'],
                defaults={
                    'first_name': user_data['first_name'],
                    'last_name': user_data['last_name'],
                    'is_active': True
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'Создан пользователь: {user.email}')
    
    def create_drugs(self):
        """Создание тестовых препаратов"""
        drugs_data = [
            {
                'mnn': 'Парацетамол',
                'trade_name': 'Парацетамол',
                'form': 'Таблетки',
                'dosage': '500 мг',
                'manufacturer': 'Фармстандарт',
                'description': 'Жаропонижающее и обезболивающее средство'
            },
            {
                'mnn': 'Ибупрофен',
                'trade_name': 'Ибупрофен',
                'form': 'Таблетки',
                'dosage': '200 мг',
                'manufacturer': 'Биохимик',
                'description': 'Противовоспалительное и обезболивающее средство'
            },
            {
                'mnn': 'Ибупрофен',
                'trade_name': 'Нурофен',
                'form': 'Таблетки',
                'dosage': '200 мг',
                'manufacturer': 'Reckitt Benckiser',
                'description': 'Обезболивающее и противовоспалительное средство'
            },
            {
                'mnn': 'Амоксициллин + Клавулановая кислота',
                'trade_name': 'Амоксиклав',
                'form': 'Таблетки',
                'dosage': '875 мг + 125 мг',
                'manufacturer': 'Sandoz',
                'description': 'Антибактериальный препарат широкого спектра'
            },
            {
                'mnn': 'Амоксициллин + Клавулановая кислота',
                'trade_name': 'Аугментин',
                'form': 'Таблетки',
                'dosage': '875 мг + 125 мг',
                'manufacturer': 'GlaxoSmithKline',
                'description': 'Антибактериальный препарат'
            },
            {
                'mnn': 'Лоратадин',
                'trade_name': 'Лоратадин',
                'form': 'Таблетки',
                'dosage': '10 мг',
                'manufacturer': 'Озон',
                'description': 'Антигистаминный препарат'
            },
            {
                'mnn': 'Лоратадин',
                'trade_name': 'Кларитин',
                'form': 'Таблетки',
                'dosage': '10 мг',
                'manufacturer': 'Bayer',
                'description': 'Против аллергии'
            },
            {
                'mnn': 'Эналаприл',
                'trade_name': 'Эналаприл',
                'form': 'Таблетки',
                'dosage': '5 мг',
                'manufacturer': 'Гедеон Рихтер',
                'description': 'Гипотензивное средство'
            },
            {
                'mnn': 'Метформин',
                'trade_name': 'Метформин',
                'form': 'Таблетки',
                'dosage': '850 мг',
                'manufacturer': 'Тева',
                'description': 'Противодиабетическое средство'
            },
            {
                'mnn': 'Омепразол',
                'trade_name': 'Омепразол',
                'form': 'Капсулы',
                'dosage': '20 мг',
                'manufacturer': 'КРКА',
                'description': 'Ингибитор протонной помпы'
            },
            {
                'mnn': 'Цетиризин',
                'trade_name': 'Цетрин',
                'form': 'Таблетки',
                'dosage': '10 мг',
                'manufacturer': 'Dr. Reddy\'s',
                'description': 'Против аллергии'
            },
            {
                'mnn': 'Аторвастатин',
                'trade_name': 'Липримар',
                'form': 'Таблетки',
                'dosage': '20 мг',
                'manufacturer': 'Pfizer',
                'description': 'Гиполипидемическое средство'
            },
            {
                'mnn': 'Аскорбиновая кислота',
                'trade_name': 'Витамин C',
                'form': 'Таблетки',
                'dosage': '500 мг',
                'manufacturer': 'Активал',
                'description': 'Витаминный препарат'
            },
            {
                'mnn': 'Дротаверин',
                'trade_name': 'Но-шпа',
                'form': 'Таблетки',
                'dosage': '40 мг',
                'manufacturer': 'Chinoin',
                'description': 'Спазмолитическое средство'
            },
            {
                'mnn': 'Аспирин',
                'trade_name': 'Аспирин',
                'form': 'Таблетки',
                'dosage': '100 мг',
                'manufacturer': 'Bayer',
                'description': 'Антиагрегантное средство'
            },
        ]
        
        drugs = []
        for drug_data in drugs_data:
            drug, created = Drug.objects.get_or_create(
                trade_name=drug_data['trade_name'],
                defaults=drug_data
            )
            if created:
                self.stdout.write(f'Создан препарат: {drug.trade_name}')
            drugs.append(drug)
        
        return drugs
    
    def create_analogues(self, drugs):
        """Создание связей аналогов"""
        analogue_groups = [
            ['Парацетамол', 'Ибупрофен', 'Нурофен', 'Аспирин'],
            ['Амоксиклав', 'Аугментин'],
            ['Лоратадин', 'Кларитин', 'Цетрин'],
            ['Эналаприл'],
            ['Метформин'],
            ['Омепразол'],
            ['Но-шпа'],
        ]
        
        for group in analogue_groups:
            group_drugs = [d for d in drugs if d.trade_name in group]
            for i in range(len(group_drugs)):
                for j in range(len(group_drugs)):
                    if i != j:
                        Analogue.objects.get_or_create(
                            original=group_drugs[i],
                            analogue=group_drugs[j],
                            defaults={'similarity_score': 0.8}
                        )
    
    def create_pharmacies(self):
        """Создание аптечных сетей и аптек"""
        networks_data = [
            {'name': 'Аптека 36.6', 'phone': '+7 (800) 555-36-36'},
            {'name': 'Ригла', 'phone': '+7 (800) 777-03-03'},
            {'name': 'Самсон-Фарма', 'phone': '+7 (495) 730-53-00'},
            {'name': 'Нео-Фарм', 'phone': '+7 (800) 333-47-47'},
            {'name': 'Аптека ИФК', 'phone': '+7 (800) 250-57-57'},
        ]
        
        networks = []
        for net_data in networks_data:
            network, created = PharmacyNetwork.objects.get_or_create(
                name=net_data['name'],
                defaults={'phone': net_data['phone']}
            )
            networks.append(network)
        
        cities = ['Москва', 'Санкт-Петербург', 'Новосибирск', 'Екатеринбург', 'Казань']
        pharmacies = []
        
        for i in range(20):
            city = random.choice(cities)
            network = random.choice(networks)
            
            street = random.choice(['Ленина', 'Пушкина', 'Гагарина', 'Советская', 'Мира'])
            address = f'{city}, ул. {street}, д. {random.randint(1, 100)}'
            
            pharmacy, created = Pharmacy.objects.get_or_create(
                name=f'Аптека #{i+1} ({network.name})',
                address=address,
                defaults={
                    'network': network,
                    'city': city,
                    'phone': f'+7 (495) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                    'working_hours': '09:00-21:00'
                }
            )
            pharmacies.append(pharmacy)
        
        return pharmacies
    
    def create_availabilities(self, drugs, pharmacies):
        """Создание наличия препаратов в аптеках"""
        base_prices = {
            'Парацетамол': 50,
            'Ибупрофен': 80,
            'Нурофен': 150,
            'Амоксиклав': 850,
            'Аугментин': 900,
            'Лоратадин': 60,
            'Кларитин': 200,
            'Эналаприл': 120,
            'Метформин': 180,
            'Омепразол': 160,
            'Цетрин': 220,
            'Липримар': 450,
            'Витамин C': 300,
            'Но-шпа': 250,
            'Аспирин': 70,
        }
        
        availability_count = 0
        for pharmacy in pharmacies:
            # Каждая аптека имеет 5-15 случайных препаратов
            num_drugs = random.randint(5, 15)
            pharmacy_drugs = random.sample(drugs, num_drugs)
            
            for drug in pharmacy_drugs:
                base_price = base_prices.get(drug.trade_name, 100)
                price = Decimal(str(random.randint(int(base_price * 0.7), int(base_price * 1.3))))
                quantity = random.choice([0, 0, 0, random.randint(1, 20)])  # 25% шанс что нет в наличии
                is_available = quantity > 0
                
                availability, created = Availability.objects.get_or_create(
                    drug=drug,
                    pharmacy=pharmacy,
                    defaults={
                        'price': price,
                        'quantity': quantity,
                        'is_available': is_available,
                        'last_updated': datetime.now() - timedelta(days=random.randint(0, 7))
                    }
                )
                
                if created:
                    availability_count += 1
                    
                    # Создаем запись в истории цен
                    PriceHistory.objects.create(
                        availability=availability,
                        price=price
                    )
        
        self.stdout.write(f'Создано {availability_count} записей о наличии препаратов')
    
    def create_subscriptions(self, drugs):
        """Создание тестовых подписок"""
        users = CustomUser.objects.all()[:3]
        
        for user in users:
            # Каждый пользователь подписывается на 2-4 препарата
            user_drugs = random.sample(drugs, random.randint(2, 4))
            
            for drug in user_drugs:
                city = random.choice(['Москва', 'Санкт-Петербург', None])
                max_price = random.choice([None, Decimal('100.00'), Decimal('200.00'), Decimal('500.00')])
                
                UserSubscription.objects.get_or_create(
                    user=user,
                    drug=drug,
                    defaults={
                        'city': city,
                        'max_price': max_price,
                        'is_active': True
                    }
                )
        
        self.stdout.write('Созданы тестовые подписки пользователей')