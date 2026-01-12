from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, UserSubscription, Drug, Pharmacy
from decimal import Decimal


class UserRegistrationForm(forms.ModelForm):
    """Форма регистрации пользователя"""
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
        help_text='Пароль должен содержать минимум 8 символов'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = CustomUser
        fields = ['email', 'first_name', 'last_name']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'email': 'Электронная почта',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
        }
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError('Пользователь с таким email уже существует')
        return email
    
    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise ValidationError({'password2': 'Пароли не совпадают'})
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class UserLoginForm(AuthenticationForm):
    """Форма входа пользователя"""
    username = forms.EmailField(
        label='Электронная почта',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autofocus': True})
    )
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].label = 'Электронная почта'
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        return username.lower()


class SubscriptionForm(forms.ModelForm):
    """Форма подписки на уведомления о наличии препарата"""
    
    class Meta:
        model = UserSubscription
        fields = ['drug', 'city', 'max_price']
        widgets = {
            'drug': forms.Select(attrs={'class': 'form-select'}),
            'city': forms.Select(attrs={'class': 'form-select'}),
            'max_price': forms.NumberInput(attrs={
                'class': 'form-control', 
                'placeholder': 'Максимальная цена (необязательно)',
                'min': '0',
                'step': '1'  # Шаг 1 рубль
            }),
        }
        labels = {
            'drug': 'Препарат',
            'city': 'Город',
            'max_price': 'Максимальная цена (руб.)',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем уникальные города из базы данных
        cities = Pharmacy.objects.values_list('city', flat=True).distinct().order_by('city')
        city_choices = [('', 'Все города')] + [(city, city) for city in cities if city]
        self.fields['city'].widget.choices = city_choices
        
        # Настраиваем поле цены
        self.fields['max_price'].widget.attrs['step'] = '1'
        
    def clean_max_price(self):
        max_price = self.cleaned_data.get('max_price')
        if max_price is not None and max_price <= 0:
            raise ValidationError('Цена должна быть положительной')
        return max_price


class SubscriptionEditForm(forms.ModelForm):
    """Форма редактирования подписки"""
    
    class Meta:
        model = UserSubscription
        fields = ['city', 'max_price', 'is_active']
        widgets = {
            'city': forms.Select(attrs={'class': 'form-select'}),
            'max_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '1'  # Шаг 1 рубль
            }),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'city': 'Город',
            'max_price': 'Максимальная цена (руб.)',
            'is_active': 'Активна',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Получаем уникальные города из базы данных
        cities = Pharmacy.objects.values_list('city', flat=True).distinct().order_by('city')
        city_choices = [('', 'Все города')] + [(city, city) for city in cities if city]
        self.fields['city'].widget.choices = city_choices
        
        # Настраиваем поле цены
        self.fields['max_price'].widget.attrs['step'] = '1'
        
    def clean_max_price(self):
        max_price = self.cleaned_data.get('max_price')
        if max_price is not None and max_price <= 0:
            raise ValidationError('Цена должна быть положительной')
        return max_price