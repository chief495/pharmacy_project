from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.mail import send_mail
from django.conf import settings


class CustomUserManager(BaseUserManager):
    """Кастомный менеджер для модели пользователя с email аутентификацией"""
    
    def create_user(self, email, password=None, **extra_fields):
        """Создание обычного пользователя"""
        if not email:
            raise ValueError('Email обязателен для регистрации')
        email = self.normalize_email(email)
        
        # Генерируем username из email если не указан
        if 'username' not in extra_fields or not extra_fields['username']:
            # Используем часть email до @ как username
            username = email.split('@')[0]
            # Убедимся, что username уникален
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            extra_fields['username'] = username
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, email, password=None, **extra_fields):
        """Создание суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    """Кастомная модель пользователя с email аутентификацией"""
    email = models.EmailField("Электронная почта", unique=True)
    username = models.CharField("Имя пользователя", max_length=150, unique=True, blank=True, null=True)
    first_name = models.CharField("Имя", max_length=150, blank=True)
    last_name = models.CharField("Фамилия", max_length=150, blank=True)
    is_staff = models.BooleanField("Сотрудник", default=False)
    is_active = models.BooleanField("Активен", default=True)
    date_joined = models.DateTimeField("Дата регистрации", auto_now_add=True)
    email_notifications = models.BooleanField("Email уведомления", default=True)
    
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Важно: добавьте username сюда
    
    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        db_table = 'custom_user'  # Явно указываем имя таблицы
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """Возвращает полное имя пользователя"""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.email
    
    def get_short_name(self):
        """Возвращает короткое имя пользователя"""
        return self.first_name or self.email
    
    def email_user(self, subject, message, from_email=None, **kwargs):
        """Отправляет email пользователю"""
        send_mail(subject, message, from_email, [self.email], **kwargs)
        
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен для регистрации')
        email = self.normalize_email(email)
        
        # Генерируем username из email если не указан
        if 'username' not in extra_fields or not extra_fields['username']:
            # Используем часть email до @ как username
            username = email.split('@')[0]
            # Проверка на username уникален
            base_username = username
            counter = 1
            while CustomUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            extra_fields['username'] = username
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user


class Drug(models.Model):
    """Модель препарата"""
    mnn = models.CharField("МНН (Международное название)", max_length=255)
    trade_name = models.CharField("Торговое название", max_length=255)
    form = models.CharField("Форма выпуска", max_length=100)
    dosage = models.CharField("Дозировка", max_length=100)
    manufacturer = models.CharField("Производитель", max_length=255)
    atx_code = models.CharField("АТХ код", max_length=20, blank=True, null=True)
    description = models.TextField("Описание", blank=True, null=True)
    created_at = models.DateTimeField("Дата добавления", auto_now_add=True)
    updated_at = models.DateTimeField("Дата обновления", auto_now=True)
    
    class Meta:
        verbose_name = "Препарат"
        verbose_name_plural = "Препараты"
        ordering = ['trade_name']
    
    def __str__(self):
        return f"{self.trade_name} ({self.mnn})"

class PharmacyNetwork(models.Model):
    """Модель аптечной сети"""
    name = models.CharField("Название сети", max_length=100)
    website = models.URLField("Сайт", blank=True, null=True)
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    is_active = models.BooleanField("Активна", default=True)
    
    class Meta:
        verbose_name = "Аптечная сеть"
        verbose_name_plural = "Аптечные сети"
    
    def __str__(self):
        return self.name

class Pharmacy(models.Model):
    """Модель конкретной аптеки"""
    network = models.ForeignKey(PharmacyNetwork, on_delete=models.CASCADE, verbose_name="Сеть")
    name = models.CharField("Название аптеки", max_length=100)
    address = models.TextField("Адрес")
    city = models.CharField("Город", max_length=100)
    phone = models.CharField("Телефон", max_length=20, blank=True, null=True)
    latitude = models.FloatField("Широта", blank=True, null=True)
    longitude = models.FloatField("Долгота", blank=True, null=True)
    working_hours = models.CharField("Часы работы", max_length=100, blank=True, null=True)
    
    class Meta:
        verbose_name = "Аптека"
        verbose_name_plural = "Аптеки"
    
    def __str__(self):
        return f"{self.name} ({self.address})"

class Availability(models.Model):
    """Модель наличия препарата в аптеке"""
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, verbose_name="Препарат")
    pharmacy = models.ForeignKey(Pharmacy, on_delete=models.CASCADE, verbose_name="Аптека")
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    quantity = models.IntegerField("Количество", default=0)
    last_updated = models.DateTimeField("Последнее обновление", auto_now=True)
    is_available = models.BooleanField("В наличии", default=True)
    
    class Meta:
        verbose_name = "Наличие препарата"
        verbose_name_plural = "Наличие препаратов"
        unique_together = ['drug', 'pharmacy']
    
    def __str__(self):
        return f"{self.drug.trade_name} в {self.pharmacy.name} - {self.price} руб."

class Analogue(models.Model):
    """Модель связи между препаратами-аналогами"""
    original = models.ForeignKey(Drug, related_name='original_drug', on_delete=models.CASCADE, verbose_name="Оригинальный препарат")
    analogue = models.ForeignKey(Drug, related_name='analogue_drug', on_delete=models.CASCADE, verbose_name="Аналог")
    similarity_score = models.FloatField("Коэффициент схожести", default=0.0)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    
    class Meta:
        verbose_name = "Аналог препарата"
        verbose_name_plural = "Аналоги препаратов"
        unique_together = ['original', 'analogue']
    
    def __str__(self):
        return f"{self.original.trade_name} → {self.analogue.trade_name}"

class PriceHistory(models.Model):
    """Модель истории изменения цен"""
    availability = models.ForeignKey(Availability, on_delete=models.CASCADE, verbose_name="Наличие")
    price = models.DecimalField("Цена", max_digits=10, decimal_places=2)
    recorded_at = models.DateTimeField("Дата записи", auto_now_add=True)
    
    class Meta:
        verbose_name = "История цены"
        verbose_name_plural = "История цен"
        ordering = ['-recorded_at']
    
    def __str__(self):
        return f"{self.availability.drug.trade_name}: {self.price} руб. ({self.recorded_at})"

class UserSubscription(models.Model):
    """Модель подписки пользователя на препарат"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name="Пользователь")
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, verbose_name="Препарат")
    city = models.CharField("Город", max_length=100, blank=True, null=True)
    max_price = models.DecimalField("Максимальная цена", max_digits=10, decimal_places=2, blank=True, null=True)
    is_active = models.BooleanField("Активна", default=True)
    created_at = models.DateTimeField("Дата создания", auto_now_add=True)
    
    class Meta:
        verbose_name = "Подписка пользователя"
        verbose_name_plural = "Подписки пользователей"
        unique_together = ['user', 'drug', 'city']
    
    def __str__(self):
        return f"{self.user.username} подписан на {self.drug.trade_name}"