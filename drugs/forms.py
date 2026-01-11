from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from .models import CustomUser, UserSubscription, Drug


class UserRegistrationForm(forms.ModelForm):
    """Форма регистрации пользователя"""
    password = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        min_length=8,
        help_text='Пароль должен содержать минимум 8 символов'
    )
    password_confirm = forms.CharField(
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
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm and password != password_confirm:
            raise ValidationError({'password_confirm': 'Пароли не совпадают'})
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
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
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Город (необязательно)'}),
            'max_price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Максимальная цена (необязательно)', 'step': '0.01'}),
        }
        labels = {
            'drug': 'Препарат',
            'city': 'Город',
            'max_price': 'Максимальная цена (руб.)',
        }


class SubscriptionEditForm(forms.ModelForm):
    """Форма редактирования подписки"""
    
    class Meta:
        model = UserSubscription
        fields = ['city', 'max_price', 'is_active']
        widgets = {
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'max_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'city': 'Город',
            'max_price': 'Максимальная цена (руб.)',
            'is_active': 'Активна',
        }
