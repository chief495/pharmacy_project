from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

def home(request):
    """Главная страница"""
    featured_drugs = [
        {
            'id': 1,
            'trade_name': 'Нурофен',
            'mnn': 'Ибупрофен',
            'form': 'таблетки',
            'dosage': '200мг',
            'manufacturer': 'Рекитт Бенкизер',
            'lowest_price': 150
        },
        {
            'id': 2,
            'trade_name': 'Парацетамол',
            'mnn': 'Парацетамол',
            'form': 'таблетки',
            'dosage': '500мг',
            'manufacturer': 'Фармстандарт',
            'lowest_price': 50
        },
        {
            'id': 3,
            'trade_name': 'Амоксиклав',
            'mnn': 'Амоксициллин',
            'form': 'таблетки',
            'dosage': '875+125мг',
            'manufacturer': 'Сандоз',
            'lowest_price': 450
        },
    ]
    
    return render(request, 'drugs/home.html', {
        'featured_drugs': featured_drugs,
        'total_drugs': 3,
        'pharmacies_count': 5,
    })

def drug_list(request):
    """Список всех препаратов"""
    drugs = [
        {
            'id': 1,
            'trade_name': 'Нурофен',
            'mnn': 'Ибупрофен',
            'form': 'таблетки',
            'dosage': '200мг',
            'manufacturer': 'Рекитт Бенкизер',
            'lowest_price': 150,
            'description': 'Нестероидный противовоспалительный препарат'
        },
        {
            'id': 2,
            'trade_name': 'Парацетамол',
            'mnn': 'Парацетамол',
            'form': 'таблетки',
            'dosage': '500мг',
            'manufacturer': 'Фармстандарт',
            'lowest_price': 50,
            'description': 'Жаропонижающее и обезболивающее средство'
        },
        {
            'id': 3,
            'trade_name': 'Амоксиклав',
            'mnn': 'Амоксициллин',
            'form': 'таблетки',
            'dosage': '875+125мг',
            'manufacturer': 'Сандоз',
            'lowest_price': 450,
            'description': 'Антибиотик широкого спектра действия'
        },
    ]
    
    query = request.GET.get('q', '')
    if query:
        drugs = [d for d in drugs if query.lower() in d['trade_name'].lower() or 
                query.lower() in d['mnn'].lower()]
    
    return render(request, 'drugs/drug_list.html', {
        'drugs': drugs,
        'total_drugs': len(drugs),
        'available_drugs': len(drugs),
        'query': query,
    })

def drug_detail(request, drug_id):
    """Детальная страница препарата"""
    drugs = {
        1: {
            'id': 1,
            'trade_name': 'Нурофен',
            'mnn': 'Ибупрофен',
            'form': 'таблетки',
            'dosage': '200мг',
            'manufacturer': 'Рекитт Бенкизер',
            'lowest_price': 150,
            'average_price': 160
        },
        2: {
            'id': 2,
            'trade_name': 'Парацетамол',
            'mnn': 'Парацетамол',
            'form': 'таблетки',
            'dosage': '500мг',
            'manufacturer': 'Фармстандарт',
            'lowest_price': 50,
            'average_price': 55
        },
        3: {
            'id': 3,
            'trade_name': 'Амоксиклав',
            'mnn': 'Амоксициллин',
            'form': 'таблетки',
            'dosage': '875+125мг',
            'manufacturer': 'Сандоз',
            'lowest_price': 450,
            'average_price': 480
        },
    }
    
    drug = drugs.get(int(drug_id))
    if not drug:
        return HttpResponse("Препарат не найден", status=404)
    
    availabilities = [
        {
            'pharmacy': {'name': 'Аптека 36.6', 'network': '36.6', 'address': 'ул. Ленина, 1', 'city': 'Москва'},
            'price': drug['lowest_price'] + 10,
            'quantity': 10,
            'last_updated': '2024-01-06 10:30:00'
        },
        {
            'pharmacy': {'name': 'ЕАптека', 'network': 'ЕАптека', 'address': 'пр. Мира, 25', 'city': 'Москва'},
            'price': drug['lowest_price'] - 5,
            'quantity': 5,
            'last_updated': '2024-01-06 09:45:00'
        },
    ]
    
    analogues = []
    if drug['mnn'] == 'Ибупрофен':
        analogues = [
            {'id': 4, 'trade_name': 'МИГ', 'mnn': 'Ибупрофен', 'form': 'таблетки', 
             'dosage': '400мг', 'lowest_price': 180},
            {'id': 5, 'trade_name': 'Фаспик', 'mnn': 'Ибупрофен', 'form': 'таблетки', 
             'dosage': '400мг', 'lowest_price': 210},
        ]
    
    return render(request, 'drugs/drug_detail.html', {
        'drug': drug,
        'availabilities': availabilities,
        'analogues': analogues,
    })

def drug_search(request):
    """Поиск препаратов"""
    query = request.GET.get('q', '')
    
    all_drugs = [
        {'id': 1, 'trade_name': 'Нурофен', 'mnn': 'Ибупрофен', 'form': 'таблетки', 
         'dosage': '200мг', 'manufacturer': 'Рекитт Бенкизер', 'lowest_price': 150},
        {'id': 2, 'trade_name': 'Парацетамол', 'mnn': 'Парацетамол', 'form': 'таблетки', 
         'dosage': '500мг', 'manufacturer': 'Фармстандарт', 'lowest_price': 50},
        {'id': 3, 'trade_name': 'Амоксиклав', 'mnn': 'Амоксициллин', 'form': 'таблетки', 
         'dosage': '875+125мг', 'manufacturer': 'Сандоз', 'lowest_price': 450},
    ]
    
    results = []
    if query:
        results = [d for d in all_drugs if query.lower() in d['trade_name'].lower() or 
                  query.lower() in d['mnn'].lower()]
    
    return render(request, 'drugs/drug_search.html', {
        'results': results,
        'query': query,
    })