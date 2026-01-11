from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from drugs import views

urlpatterns = [
    # Главная страница
    path('', views.home, name='home'),
    
    # Админка Django
    path('admin/', admin.site.urls),
    
    # Подключаем URL из приложения drugs (включая аутентификацию)
    path('drugs/', include('drugs.urls')),
    
    # Аутентификация (для совместимости с LOGIN_URL='login')
    path('accounts/login/', views.user_login, name='login'),
    path('accounts/logout/', views.user_logout, name='logout'),
    path('accounts/register/', views.register, name='register'),
]

# Обслуживание медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)