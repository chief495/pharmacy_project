from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Min, Avg, Count, Q
from django.core.mail import send_mail
from django.conf import settings
from .models import Drug, Availability, Analogue, UserSubscription, Pharmacy, PharmacyNetwork
from .forms import UserRegistrationForm, UserLoginForm, SubscriptionForm, SubscriptionEditForm
from decimal import Decimal
from datetime import datetime, timedelta

def home(request):
    """Главная страница"""
    # Получаем препараты с минимальной ценой и количеством аптек
    featured_drugs = Drug.objects.annotate(
        min_price=Min('availability__price'),
        pharmacy_count=Count('availability', distinct=True)
    ).filter(
        availability__is_available=True
    ).order_by('?')[:6]  # Случайные 6 препаратов
    
    total_drugs = Drug.objects.count()
    pharmacies_count = Pharmacy.objects.count()
    
    return render(request, 'drugs/home.html', {
        'featured_drugs': featured_drugs,
        'total_drugs': total_drugs,
        'pharmacies_count': pharmacies_count,
    })

def drug_list(request):
    """Список всех препаратов"""
    query = request.GET.get('q', '')
    
    drugs = Drug.objects.annotate(
        min_price=Min('availability__price'),
        pharmacy_count=Count('availability', distinct=True)
    ).all()
    
    if query:
        drugs = drugs.filter(
            Q(trade_name__icontains=query) |
            Q(mnn__icontains=query) |
            Q(manufacturer__icontains=query)
        )
    
    drugs = drugs.order_by('trade_name')
    
    available_drugs = drugs.filter(availability__is_available=True).distinct().count()
    
    return render(request, 'drugs/drug_list.html', {
        'drugs': drugs,
        'total_drugs': drugs.count(),
        'available_drugs': available_drugs,
        'query': query,
    })

def drug_detail(request, drug_id):
    """Детальная страница препарата"""
    drug = get_object_or_404(
        Drug.objects.annotate(
            min_price=Min('availability__price'),
            avg_price=Avg('availability__price')
        ),
        id=drug_id
    )
    
    # Получаем наличие препарата в аптеках
    availabilities = Availability.objects.filter(
        drug=drug,
        is_available=True
    ).select_related('pharmacy', 'pharmacy__network').order_by('price')
    
    # Получаем аналоги препарата
    analogues_ids = Analogue.objects.filter(
        Q(original=drug) | Q(analogue=drug)
    ).values_list('original_id', 'analogue_id')
    
    analogue_ids = set()
    for orig_id, anal_id in analogues_ids:
        if orig_id == drug.id:
            analogue_ids.add(anal_id)
        else:
            analogue_ids.add(orig_id)
    
    analogues = Drug.objects.filter(id__in=analogue_ids).annotate(
        min_price=Min('availability__price')
    ).distinct()[:10]
    
    # Проверяем, подписан ли пользователь на этот препарат
    user_subscription = None
    if request.user.is_authenticated:
        user_subscription = UserSubscription.objects.filter(
            user=request.user,
            drug=drug,
            is_active=True
        ).first()
    
    return render(request, 'drugs/drug_detail.html', {
        'drug': drug,
        'availabilities': availabilities,
        'analogues': analogues,
        'user_subscription': user_subscription,
    })

def drug_search(request):
    """Поиск препаратов"""
    query = request.GET.get('q', '')
    
    results = Drug.objects.none()
    
    if query:
        results = Drug.objects.annotate(
            min_price=Min('availability__price')
        ).filter(
            Q(trade_name__icontains=query) |
            Q(mnn__icontains=query) |
            Q(manufacturer__icontains=query) |
            Q(description__icontains=query)
        ).order_by('trade_name')
    
    return render(request, 'drugs/drug_search.html', {
        'results': results,
        'query': query,
    })


def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            
            # Автоматически логиним пользователя
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            login(request, user)
            
            messages.success(request, f'Добро пожаловать, {user.get_full_name()}! Регистрация прошла успешно.')
            return redirect('drugs:drug_list')  # Используйте правильное имя URL
    else:
        form = UserRegistrationForm()
    
    return render(request, 'drugs/register.html', {'form': form})


def user_login(request):
    """Вход пользователя"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = UserLoginForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name()}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
    else:
        form = UserLoginForm()
    
    return render(request, 'drugs/login.html', {'form': form})


def user_logout(request):
    """Выход пользователя"""
    logout(request)
    messages.info(request, 'Вы успешно вышли из системы.')
    return redirect('home')


@login_required
def my_subscriptions(request):
    """Страница подписок пользователя"""
    subscriptions = UserSubscription.objects.filter(user=request.user).select_related('drug')
    
    return render(request, 'drugs/my_subscriptions.html', {
        'subscriptions': subscriptions,
    })


@login_required
def subscribe(request, drug_id=None):
    """Создание подписки на препарат"""
    drug = None
    if drug_id:
        drug = get_object_or_404(Drug, id=drug_id)
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            subscription.save()
            messages.success(request, f'Вы подписались на уведомления о препарате {subscription.drug.trade_name}.')
            return redirect('my_subscriptions')
    else:
        initial = {}
        if drug:
            initial['drug'] = drug
        form = SubscriptionForm(initial=initial)
    
    return render(request, 'drugs/subscribe.html', {
        'form': form,
        'drug': drug,
    })


@login_required
def unsubscribe(request, subscription_id):
    """Удаление подписки"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
    if request.method == 'POST':
        drug_name = subscription.drug.trade_name
        subscription.delete()
        messages.success(request, f'Вы отписались от уведомлений о препарате {drug_name}.')
        return redirect('my_subscriptions')
    
    return render(request, 'drugs/unsubscribe.html', {'subscription': subscription})


@login_required
def edit_subscription(request, subscription_id):
    """Редактирование подписки"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        form = SubscriptionEditForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            messages.success(request, 'Подписка обновлена.')
            return redirect('my_subscriptions')
    else:
        form = SubscriptionEditForm(instance=subscription)
    
    return render(request, 'drugs/edit_subscription.html', {
        'form': form,
        'subscription': subscription,
    })


def send_availability_notifications(drug_id=None):
    """
    Отправка уведомлений о наличии препаратов подписанным пользователям.
    Можно вызывать через management command или cron.
    """
    from django.db.models import Q
    
    subscriptions_query = UserSubscription.objects.filter(is_active=True).select_related('user', 'drug')
    
    if drug_id:
        subscriptions_query = subscriptions_query.filter(drug_id=drug_id)
    
    notifications_sent = 0
    
    for subscription in subscriptions_query:
        # Проверяем наличие препарата
        availabilities_query = Availability.objects.filter(
            drug=subscription.drug,
            is_available=True
        ).select_related('pharmacy', 'drug')
        
        # Фильтруем по городу, если указан
        if subscription.city:
            availabilities_query = availabilities_query.filter(pharmacy__city=subscription.city)
        
        # Фильтруем по максимальной цене, если указана
        if subscription.max_price:
            availabilities_query = availabilities_query.filter(price__lte=subscription.max_price)
        
        availabilities = list(availabilities_query[:10])  # Ограничиваем до 10 аптек
        
        if availabilities and subscription.user.email_notifications:
            # Формируем сообщение
            subject = f'Наличие препарата {subscription.drug.trade_name}'
            
            message_parts = [
                f'Здравствуйте, {subscription.user.get_full_name()}!',
                '',
                f'Препарат {subscription.drug.trade_name} ({subscription.drug.mnn}) теперь доступен:',
                '',
            ]
            
            for availability in availabilities:
                message_parts.append(
                    f"• {availability.pharmacy.name} ({availability.pharmacy.address})"
                )
                message_parts.append(f"  Цена: {availability.price} руб.")
                if availability.quantity > 0:
                    message_parts.append(f"  В наличии: {availability.quantity} шт.")
                message_parts.append('')
            
            message_parts.append(f'Просмотреть подробности: {settings.SITE_URL if hasattr(settings, "SITE_URL") else ""}/drugs/{subscription.drug.id}/')
            message_parts.append('')
            message_parts.append('---')
            message_parts.append('Вы получили это письмо, так как подписаны на уведомления о наличии препаратов.')
            
            message = '\n'.join(message_parts)
            
            try:
                subscription.user.email_user(
                    subject,
                    message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    fail_silently=False,
                )
                notifications_sent += 1
            except Exception as e:
                # Логируем ошибку, но продолжаем обработку других подписок
                print(f"Error sending email to {subscription.user.email}: {e}")
    
    return notifications_sent

@login_required
def create_test_data(request):
    """Создание тестовых данных для демонстрации"""
    if not request.user.is_staff:
        messages.error(request, 'Эта функция доступна только администраторам.')
        return redirect('home')
    
    import random
    from decimal import Decimal
    from datetime import datetime, timedelta
    
    try:
        # 1. Создаем препараты
        drugs_data = [
            {'trade_name': 'Парацетамол', 'mnn': 'Парацетамол', 'form': 'Таблетки', 'dosage': '500 мг', 'manufacturer': 'Фармстандарт'},
            {'trade_name': 'Ибупрофен', 'mnn': 'Ибупрофен', 'form': 'Таблетки', 'dosage': '200 мг', 'manufacturer': 'Биохимик'},
            {'trade_name': 'Нурофен', 'mnn': 'Ибупрофен', 'form': 'Таблетки', 'dosage': '200 мг', 'manufacturer': 'Reckitt'},
            {'trade_name': 'Амоксиклав', 'mnn': 'Амоксициллин', 'form': 'Таблетки', 'dosage': '875 мг', 'manufacturer': 'Sandoz'},
            {'trade_name': 'Лоратадин', 'mnn': 'Лоратадин', 'form': 'Таблетки', 'dosage': '10 мг', 'manufacturer': 'Озон'},
            {'trade_name': 'Кларитин', 'mnn': 'Лоратадин', 'form': 'Таблетки', 'dosage': '10 мг', 'manufacturer': 'Bayer'},
            {'trade_name': 'Эналаприл', 'mnn': 'Эналаприл', 'form': 'Таблетки', 'dosage': '5 мг', 'manufacturer': 'Gedeon Richter'},
            {'trade_name': 'Метформин', 'mnn': 'Метформин', 'form': 'Таблетки', 'dosage': '850 мг', 'manufacturer': 'Teva'},
            {'trade_name': 'Омепразол', 'mnn': 'Омепразол', 'form': 'Капсулы', 'dosage': '20 мг', 'manufacturer': 'KRKA'},
            {'trade_name': 'Аспирин', 'mnn': 'Ацетилсалициловая кислота', 'form': 'Таблетки', 'dosage': '100 мг', 'manufacturer': 'Bayer'},
        ]
        
        drugs = []
        for data in drugs_data:
            drug, created = Drug.objects.get_or_create(
                trade_name=data['trade_name'],
                defaults=data
            )
            drugs.append(drug)
        
        # 2. Создаем аналоги
        analogue_groups = [
            ['Парацетамол', 'Ибупрофен', 'Нурофен', 'Аспирин'],
            ['Амоксиклав'],
            ['Лоратадин', 'Кларитин'],
            ['Эналаприл'],
            ['Метформин'],
            ['Омепразол'],
        ]
        
        for group in analogue_groups:
            group_drugs = [d for d in drugs if d.trade_name in group]
            for i in range(len(group_drugs)):
                for j in range(len(group_drugs)):
                    if i != j and not Analogue.objects.filter(original=group_drugs[i], analogue=group_drugs[j]).exists():
                        Analogue.objects.create(
                            original=group_drugs[i],
                            analogue=group_drugs[j],
                            similarity_score=random.uniform(0.7, 0.9)
                        )
        
        # 3. Создаем аптечные сети
        networks_data = [
            {'name': 'Аптека 36.6', 'phone': '+7 (800) 555-36-36'},
            {'name': 'Ригла', 'phone': '+7 (800) 777-03-03'},
            {'name': 'Самсон-Фарма', 'phone': '+7 (495) 730-53-00'},
        ]
        
        networks = []
        for net_data in networks_data:
            network, created = PharmacyNetwork.objects.get_or_create(
                name=net_data['name'],
                defaults={'phone': net_data['phone']}
            )
            networks.append(network)
        
        # 4. Создаем аптеки
        cities = ['Москва', 'Санкт-Петербург', 'Казань', 'Екатеринбург']
        pharmacies = []
        
        for i in range(10):
            city = random.choice(cities)
            network = random.choice(networks)
            
            pharmacy, created = Pharmacy.objects.get_or_create(
                name=f'Аптека {i+1} ({network.name})',
                city=city,
                defaults={
                    'network': network,
                    'address': f'{city}, ул. Примерная, д. {random.randint(1, 100)}',
                    'phone': f'+7 (495) {random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}',
                    'working_hours': '09:00-21:00'
                }
            )
            pharmacies.append(pharmacy)
        
        # 5. Создаем наличие препаратов
        base_prices = {
            'Парацетамол': 50, 'Ибупрофен': 80, 'Нурофен': 150,
            'Амоксиклав': 850, 'Лоратадин': 60, 'Кларитин': 200,
            'Эналаприл': 120, 'Метформин': 180, 'Омепразол': 160, 'Аспирин': 70
        }
        
        availability_count = 0
        for pharmacy in pharmacies:
            for drug in random.sample(drugs, random.randint(3, 7)):
                base_price = base_prices.get(drug.trade_name, 100)
                price = Decimal(str(random.randint(int(base_price * 0.8), int(base_price * 1.2))))
                quantity = random.choice([0, 0, random.randint(1, 20)])  # 33% шанс что нет в наличии
                
                availability, created = Availability.objects.get_or_create(
                    drug=drug,
                    pharmacy=pharmacy,
                    defaults={
                        'price': price,
                        'quantity': quantity,
                        'is_available': quantity > 0,
                        'last_updated': datetime.now() - timedelta(days=random.randint(0, 3))
                    }
                )
                if created:
                    availability_count += 1
        
        # 6. Создаем тестовую подписку для текущего пользователя
        if drugs:
            test_drug = random.choice(drugs)
            UserSubscription.objects.get_or_create(
                user=request.user,
                drug=test_drug,
                defaults={
                    'city': 'Москва',
                    'max_price': Decimal('100.00'),
                    'is_active': True
                }
            )
        
        messages.success(request, 
            f'✅ Создано: {len(drugs)} препаратов, {len(pharmacies)} аптек, {availability_count} записей о наличии')
        
    except Exception as e:
        messages.error(request, f'❌ Ошибка: {str(e)}')
    
    return redirect('home')


@login_required
def test_notifications(request):
    """Тест отправки уведомлений"""
    if not request.user.is_staff:
        messages.error(request, 'Эта функция доступна только администраторам.')
        return redirect('home')
    
    try:
        # Создаем тестовое наличие для проверки
        drug = Drug.objects.first()
        if drug:
            # Добавляем наличие для теста
            moscow_pharmacies = Pharmacy.objects.filter(city='Москва')[:2]
            for pharmacy in moscow_pharmacies:
                Availability.objects.get_or_create(
                    drug=drug,
                    pharmacy=pharmacy,
                    defaults={
                        'price': Decimal('50.00'),
                        'quantity': 10,
                        'is_available': True,
                        'last_updated': datetime.now()
                    }
                )
            
            # Создаем или обновляем подписку
            subscription, created = UserSubscription.objects.get_or_create(
                user=request.user,
                drug=drug,
                defaults={
                    'city': 'Москва',
                    'max_price': Decimal('100.00'),
                    'is_active': True
                }
            )
            
            # Отправляем уведомление
            notifications_sent = send_availability_notifications(drug.id)
            
            if notifications_sent > 0:
                messages.success(request, f'📧 Тестовое уведомление отправлено на {request.user.email}')
            else:
                messages.warning(request, '⚠️ Уведомление не отправлено. Проверьте настройки email.')
        else:
            messages.error(request, '❌ Нет препаратов. Сначала создайте тестовые данные.')
    except Exception as e:
        messages.error(request, f'❌ Ошибка: {str(e)}')
    
    return redirect('home')