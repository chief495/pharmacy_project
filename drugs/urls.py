from django.urls import path
from . import views

app_name = 'drugs'

urlpatterns = [
    path('', views.drug_list, name='drug_list'),
    path('search/', views.drug_search, name='drug_search'),
    path('<int:drug_id>/', views.drug_detail, name='drug_detail'),
    
    # Аутентификация
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    
    # Подписки
    path('subscriptions/', views.my_subscriptions, name='my_subscriptions'),
    path('subscribe/', views.subscribe, name='subscribe'),
    path('subscribe/<int:drug_id>/', views.subscribe, name='subscribe_drug'),
    path('subscriptions/<int:subscription_id>/edit/', views.edit_subscription, name='edit_subscription'),
    path('subscriptions/<int:subscription_id>/unsubscribe/', views.unsubscribe, name='unsubscribe'),
    
    # Для тестирования
    path('create-test-data/', views.create_test_data, name='create_test_data'),
    path('test-notifications/', views.test_notifications, name='test_notifications'),
]