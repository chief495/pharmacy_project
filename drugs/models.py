from django.db import models
from django.contrib.auth.models import User

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
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
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