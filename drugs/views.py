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
from random import random
import logging

logger = logging.getLogger(__name__)

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
            avg_price=Avg('availability__price'),
            pharmacy_count=Count('availability', distinct=True)
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
    
    # Проверяем, есть ли препарат в наличии (для отображения в шаблоне)
    is_available = availabilities.exists()
    # Берем только первые 2 аптеки для отображения
    first_availabilities = availabilities[:2]
    
    return render(request, 'drugs/drug_detail.html', {
        'drug': drug,
        'availabilities': availabilities,
        'first_availabilities': first_availabilities,
        'is_available': is_available,
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

logger = logging.getLogger(__name__)

def register(request):
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        logger.debug(f'Данные формы: {request.POST}')
        logger.debug(f'Форма валидна: {form.is_valid()}')
        logger.debug(f'Ошибки формы: {form.errors}')
        
        if form.is_valid():
            try:
                user = form.save()
                logger.info(f'Пользователь создан: {user.email}')
                
                # Автоматически логиним пользователя
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request, user)
                
                messages.success(request, f'Добро пожаловать, {user.get_full_name()}! Регистрация прошла успешно.')
                return redirect('drugs:drug_list')
            except Exception as e:
                logger.error(f'Ошибка при создании пользователя: {e}')
                messages.error(request, f'Произошла ошибка при регистрации: {e}')
        else:
            # Показываем ошибки пользователю
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
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
            # Добавляем сообщение об ошибке
            messages.error(request, 'Неверный email или пароль. Попробуйте еще раз.')
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
    """Создание подписки на препарат с немедленной отправкой уведомления если есть в наличии"""
    drug = None
    
    if drug_id:
        drug = get_object_or_404(Drug, id=drug_id)
    
    if request.method == 'POST':
        form = SubscriptionForm(request.POST)
        if form.is_valid():
            subscription = form.save(commit=False)
            subscription.user = request.user
            
            # Проверяем, нет ли уже такой подписки
            existing_subscription = UserSubscription.objects.filter(
                user=request.user,
                drug=subscription.drug,
                city=subscription.city
            ).first()
            
            if existing_subscription:
                messages.warning(request, f'Вы уже подписаны на этот препарат с такими параметрами.')
                return redirect('drugs:my_subscriptions')
            
            subscription.save()
            
            # НЕМЕДЛЕННО проверяем наличие и отправляем уведомление если есть
            send_immediate_notification(subscription)
            
            messages.success(request, f'Вы подписались на уведомления о препарате {subscription.drug.trade_name}.')
            return redirect('drugs:my_subscriptions')
    else:
        initial = {}
        if drug:
            initial['drug'] = drug
        form = SubscriptionForm(initial=initial)
    
    return render(request, 'drugs/subscribe.html', {
        'form': form,
        'drug': drug,
    })
    
def send_immediate_notification(subscription):
    """Немедленная отправка уведомления если препарат есть в наличии по фильтрам"""
    from django.core.mail import send_mail
    from django.conf import settings
    import logging
    
    logger = logging.getLogger(__name__)
    
    try:
        # Проверяем наличие препарата по критериям подписки
        availabilities_query = Availability.objects.filter(
            drug=subscription.drug,
            is_available=True
        ).select_related('pharmacy')
        
        if subscription.city:
            availabilities_query = availabilities_query.filter(pharmacy__city=subscription.city)
        
        if subscription.max_price:
            availabilities_query = availabilities_query.filter(price__lte=subscription.max_price)
        
        availabilities = list(availabilities_query.order_by('price')[:10])  # Топ 10 самых дешевых
        
        if availabilities:
            # Формируем заголовок в зависимости от фильтров
            if subscription.city:
                subject = f'✅ {subscription.drug.trade_name} в наличии в {subscription.city}!'
            else:
                subject = f'✅ {subscription.drug.trade_name} уже в наличии!'
            
            message_lines = [
                f'Здравствуйте, {subscription.user.get_full_name()}!',
                '',
                f'Препарат {subscription.drug.trade_name} ({subscription.drug.mnn}) доступен:',
                '',
            ]
            
            # Добавляем информацию о фильтрах
            if subscription.city or subscription.max_price:
                message_lines.append('По вашим критериям:')
                if subscription.city:
                    message_lines.append(f'• Город: {subscription.city}')
                if subscription.max_price:
                    message_lines.append(f'• Максимальная цена: до {subscription.max_price} руб.')
                message_lines.append('')
            
            message_lines.append('Найдены следующие предложения:')
            message_lines.append('')
            
            for avail in availabilities:
                message_lines.append(f'🏥 {avail.pharmacy.name}')
                message_lines.append(f'📍 {avail.pharmacy.address}, {avail.pharmacy.city}')
                message_lines.append(f'💰 Цена: {avail.price} руб.')
                if avail.quantity > 0:
                    message_lines.append(f'📦 В наличии: {avail.quantity} шт.')
                message_lines.append('')
            
            site_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            message_lines.append(f'🔗 Подробнее о препарате: {site_url}/drugs/{subscription.drug.id}/')
            message_lines.append('')
            message_lines.append('---')
            message_lines.append('Это автоматическое уведомление о текущем наличии.')
            message_lines.append('Вы будете получать уведомления при появлении новых поступлений.')
            message_lines.append('Чтобы изменить параметры подписки, перейдите в "Мои подписки".')
            
            message = '\n'.join(message_lines)
            
            # Отправляем email
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [subscription.user.email],
                fail_silently=False,
            )
            
            logger.info(f'Немедленное уведомление отправлено {subscription.user.email} о {subscription.drug.trade_name}')
            return True
        
        else:
            # Записываем почему не отправили
            reason = "нет в наличии"
            if subscription.city:
                reason = f"нет в городе {subscription.city}"
            if subscription.max_price:
                reason = f"нет по цене до {subscription.max_price} руб."
            logger.info(f'Нет текущего наличия для {subscription.user.email} о {subscription.drug.trade_name} ({reason})')
            return False
            
    except Exception as e:
        logger.error(f'Ошибка при отправке немедленного уведомления: {e}')
        return False

@login_required
def unsubscribe(request, subscription_id):
    """Удаление подписки"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
    
    if request.method == 'POST':
        drug_name = subscription.drug.trade_name
        subscription.delete()
        messages.success(request, f'Вы отписались от уведомлений о препарате {drug_name}.')
        return redirect('drugs:my_subscriptions')
    
    # GET запрос - показываем страницу подтверждения
    return render(request, 'drugs/unsubscribe.html', {'subscription': subscription})


@login_required
def edit_subscription(request, subscription_id):
    """Редактирование подписки с проверкой наличия"""
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)
    
    old_city = subscription.city
    old_max_price = subscription.max_price
    
    if request.method == 'POST':
        form = SubscriptionEditForm(request.POST, instance=subscription)
        if form.is_valid():
            form.save()
            
            # Проверяем, изменились ли фильтры
            subscription.refresh_from_db()
            filters_changed = (old_city != subscription.city) or (old_max_price != subscription.max_price)
            
            # Если фильтры изменились или подписка стала активной, проверяем наличие
            if filters_changed or subscription.is_active:
                send_immediate_notification(subscription)
            
            messages.success(request, 'Подписка обновлена.')
            return redirect('drugs:my_subscriptions')
    else:
        form = SubscriptionEditForm(instance=subscription)
    
    return render(request, 'drugs/edit_subscription.html', {
        'form': form,
        'subscription': subscription,
    })

@login_required
def check_my_subscriptions(request):
    """Проверяет наличие для всех подписок пользователя"""
    subscriptions = UserSubscription.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('drug')
    
    notifications_sent = 0
    
    for subscription in subscriptions:
        # Используем вашу существующую функцию
        if send_immediate_notification(subscription):
            notifications_sent += 1
    
    if notifications_sent > 0:
        messages.success(request, f'✅ Проверка завершена. Отправлено {notifications_sent} уведомлений.')
    else:
        messages.info(request, 'ℹ️ Для ваших подписок нет новых предложений.')
    
    return redirect('drugs:my_subscriptions')

def send_availability_notifications(drug_id=None):
    """
    Отправка уведомлений о наличии препаратов подписанным пользователям.
    Можно вызывать через management command или cron.
    """
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