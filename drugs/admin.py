from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    CustomUser, Drug, PharmacyNetwork, Pharmacy, Availability,
    Analogue, PriceHistory, UserSubscription
)


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """Административная панель для кастомной модели пользователя"""
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined', 'email_notifications')
    list_filter = ('is_staff', 'is_active', 'email_notifications', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Дополнительно', {'fields': ('email_notifications',)}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Дополнительно', {'fields': ('email_notifications',)}),
    )


@admin.register(Drug)
class DrugAdmin(admin.ModelAdmin):
    """Административная панель для препаратов"""
    list_display = ('trade_name', 'mnn', 'form', 'dosage', 'manufacturer', 'created_at')
    list_filter = ('form', 'manufacturer', 'created_at')
    search_fields = ('trade_name', 'mnn', 'manufacturer', 'atx_code')
    ordering = ('trade_name',)
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Основная информация', {
            'fields': ('trade_name', 'mnn', 'form', 'dosage', 'manufacturer')
        }),
        ('Дополнительная информация', {
            'fields': ('atx_code', 'description')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PharmacyNetwork)
class PharmacyNetworkAdmin(admin.ModelAdmin):
    """Административная панель для аптечных сетей"""
    list_display = ('name', 'website', 'phone', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'website', 'phone')
    ordering = ('name',)


@admin.register(Pharmacy)
class PharmacyAdmin(admin.ModelAdmin):
    """Административная панель для аптек"""
    list_display = ('name', 'network', 'city', 'address', 'phone')
    list_filter = ('network', 'city')
    search_fields = ('name', 'address', 'city', 'phone')
    ordering = ('city', 'name')
    raw_id_fields = ('network',)


@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """Административная панель для наличия препаратов"""
    list_display = ('drug', 'pharmacy', 'price', 'quantity', 'is_available', 'last_updated')
    list_filter = ('is_available', 'last_updated', 'pharmacy__city')
    search_fields = ('drug__trade_name', 'drug__mnn', 'pharmacy__name', 'pharmacy__city')
    ordering = ('-last_updated',)
    raw_id_fields = ('drug', 'pharmacy')
    readonly_fields = ('last_updated',)
    list_editable = ('price', 'quantity', 'is_available')


@admin.register(Analogue)
class AnalogueAdmin(admin.ModelAdmin):
    """Административная панель для аналогов препаратов"""
    list_display = ('original', 'analogue', 'similarity_score', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('original__trade_name', 'original__mnn', 'analogue__trade_name', 'analogue__mnn')
    ordering = ('-created_at',)
    raw_id_fields = ('original', 'analogue')
    readonly_fields = ('created_at',)


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    """Административная панель для истории цен"""
    list_display = ('availability', 'price', 'recorded_at')
    list_filter = ('recorded_at',)
    search_fields = ('availability__drug__trade_name', 'availability__pharmacy__name')
    ordering = ('-recorded_at',)
    raw_id_fields = ('availability',)
    readonly_fields = ('recorded_at',)
    date_hierarchy = 'recorded_at'


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    """Административная панель для подписок пользователей"""
    list_display = ('user', 'drug', 'city', 'max_price', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'city')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'drug__trade_name', 'drug__mnn', 'city')
    ordering = ('-created_at',)
    raw_id_fields = ('user', 'drug')
    readonly_fields = ('created_at',)
    list_editable = ('is_active',)
