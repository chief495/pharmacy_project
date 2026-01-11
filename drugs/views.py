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
            
            # Явно указываем бэкенд аутентификации
            user.backend = 'django.contrib.auth.backends.ModelBackend'
            
            login(request, user)
            messages.success(request, f'Добро пожаловать, {user.get_full_name()}! Регистрация прошла успешно.')
            return redirect('home')
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
