from django.urls import path
from . import views  # импортируем views из текущего приложения

app_name = 'drugs'  # пространство имен для приложения

urlpatterns = [
    path('', views.drug_list, name='drug_list'),  # список препаратов
    path('search/', views.drug_search, name='drug_search'),  # поиск
    path('<int:drug_id>/', views.drug_detail, name='drug_detail'),  # детали препарата
]