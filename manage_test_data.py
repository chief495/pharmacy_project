#!/usr/bin/env python
import os
import sys
import django

# Настройка Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pharmacy.settings')
django.setup()

def create_test_data_interactive():
    """Интерактивное создание тестовых данных"""
    from drugs.models import Drug, Pharmacy, Availability, CustomUser
    
    print("=" * 50)
    print("СОЗДАНИЕ ТЕСТОВЫХ ДАННЫХ")
    print("=" * 50)
    
    # Проверяем текущие данные
    print(f"\nТекущая база данных:")
    print(f"• Препаратов: {Drug.objects.count()}")
    print(f"• Аптек: {Pharmacy.objects.count()}")
    print(f"• Наличие: {Availability.objects.count()}")
    print(f"• Пользователей: {CustomUser.objects.count()}")
    
    # Спрашиваем подтверждение
    response = input("\nСоздать тестовые данные? (y/n): ")
    
    if response.lower() == 'y':
        # Импортируем и запускаем view
        from django.test import RequestFactory
        from django.contrib.auth import get_user_model
        
        # Создаем фиктивный запрос
        factory = RequestFactory()
        request = factory.get('/create-test-data/')
        
        # Находим или создаем администратора
        User = get_user_model()
        admin_user = User.objects.filter(is_staff=True).first()
        if not admin_user:
            print("\n❌ Нет пользователя с правами администратора!")
            print("Сначала создайте суперпользователя:")
            print("python manage.py createsuperuser")
            return
        
        request.user = admin_user
        
        # Вызываем нашу функцию
        from drugs.views import create_test_data
        from django.contrib import messages
        
        # Создаем хранилище сообщений
        storage = messages.get_messages(request)
        storage.used = True
        
        response = create_test_data(request)
        
        # Выводим сообщения
        print("\nРезультат:")
        for message in storage:
            print(f"• {message}")
        
        print("\nТестовые данные созданы!")
        print("\nДля входа используйте:")
        print(f"Email: {admin_user.email}")
        print("Пароль: (тот, который вы указали при создании)")
    
    else:
        print("\nОперация отменена")

if __name__ == '__main__':
    create_test_data_interactive()