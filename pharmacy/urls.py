from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView  # для статических страниц
from drugs import views  # Импортируем views из приложения drugs

urlpatterns = [
    # Главная страница - используем нашу функцию home из drugs/views.py
    path('', views.home, name='home'),
    
    # Админка Django
    path('admin/', admin.site.urls),
    
    # Подключаем URL из приложения drugs
    path('drugs/', include('drugs.urls')),
    
    # Можно добавить статические страницы
    path('about/', TemplateView.as_view(template_name='about.html'), name='about'),
]