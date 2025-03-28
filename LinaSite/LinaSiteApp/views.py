from django.shortcuts import render

# Create your views here.

def index(request):
    """
    Основная страница приложения.
    """
    return render(request, 'DonorInfo.html')


# views.py
from django.shortcuts import render
from django.http import JsonResponse
from .models import Donor, BloodComponent, Donation
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404


def donor_search(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Получаем параметры поиска из POST-запроса
        blood_group = request.POST.get('blood_group', '')
        rh_factor = request.POST.get('rh_factor', '')
        kell_factor = request.POST.get('kell_factor', '')
        name_query = request.POST.get('name', '')
        components = request.POST.getlist('components[]', [])

        # Начинаем формировать запрос
        queryset = Donor.objects.all()

        # Фильтрация по группе крови
        if blood_group:
            queryset = queryset.filter(blood_group=blood_group)

        # Фильтрация по Rh-фактору (если не "Любой")
        if rh_factor and rh_factor != 'any':
            queryset = queryset.filter(rh_factor=rh_factor)

        # Фильтрация по Kell-фактору (если не "Любой")
        if kell_factor and kell_factor != 'any':
            queryset = queryset.filter(kell_factor=kell_factor)

        # Поиск по ФИО
        if name_query:
            queryset = queryset.filter(
                Q(last_name__icontains=name_query) |
                Q(first_name__icontains=name_query) |
                Q(middle_name__icontains=name_query)
            )

        # Поиск по компонентам крови
        if components:
            queryset = queryset.filter(blood_components__name__in=components).distinct()

        # Подготавливаем данные для ответа
        donors_data = []
        for donor in queryset[:5]:  # Ограничиваем результат пятью записями
            # Получаем компоненты крови для данного донора
            donor_components = [comp.name for comp in donor.blood_components.all()]

            donors_data.append({
                'id': donor.id,
                'full_name': donor.get_full_name(),
                'blood_info': f"{donor.blood_group} ({donor.rh_factor})",
                'components': donor_components,
                'is_regular': donor.is_regular,
                'donation_count': donor.donation_count
            })

        return JsonResponse({'donors': donors_data})

    # Для GET-запроса просто возвращаем страницу с формой поиска
    blood_components = BloodComponent.objects.all()
    return render(request, 'donor_search.html', {'blood_components': blood_components})


def donation_register(request):
    if request.method == 'POST':
        # Обработка формы
        donor_id = request.POST.get('donor')
        donation_date = request.POST.get('donation_date')
        donation_type = request.POST.get('donation_type')
        payment_type = request.POST.get('payment_type')
        is_first_donation = request.POST.get('is_first_donation') == 'on'
        document_number = request.POST.get('document_number')
        documents_changed = request.POST.get('documents_changed') == 'on'
        donation_location = request.POST.get('donation_location')
        donation_address = request.POST.get('donation_address')
        contraindications = request.POST.get('contraindications')
        contraindication_details = request.POST.get('contraindication_details')
        directions_needed = request.POST.get('directions_needed')
        directions_details = request.POST.get('directions_details')
        component_ids = request.POST.getlist('components')

        # Создаем донацию
        donor = get_object_or_404(Donor, id=donor_id)
        donation = Donation.objects.create(
            donor=donor,
            donation_date=donation_date,
            donation_type=donation_type,
            payment_type=payment_type,
            is_first_donation=is_first_donation,
            document_number=document_number,
            documents_changed=documents_changed,
            donation_location=donation_location,
            donation_address=donation_address,
            contraindications=contraindications,
            contraindication_details=contraindication_details,
            directions_needed=directions_needed,
            directions_details=directions_details
        )

        # Добавляем компоненты
        if component_ids:
            donation.components.set(component_ids)

        # Увеличиваем количество донаций донора
        donor.donation_count += 1
        donor.save()

        return redirect('donation_list')  # Перенаправляем на список донаций

    # Для GET-запроса отображаем форму
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    blood_components = BloodComponent.objects.all()

    return render(request, 'donation_register.html', {
        'donors': donors,
        'blood_components': blood_components,
    })


def get_donor_info(request, donor_id):
    """API для получения информации о доноре"""
    try:
        donor = Donor.objects.get(id=donor_id)
        return JsonResponse({
            'success': True,
            'snils': donor.snils,
            'full_name': donor.get_full_name(),
            'blood_group': donor.blood_group,
            'rh_factor': donor.rh_factor,
            'kell_factor': donor.kell_factor,
            'last_weight': str(donor.last_weight),
            'last_pressure': donor.last_pressure,
            'address': donor.address if hasattr(donor, 'address') else '',
            'document_number': donor.document_number if hasattr(donor, 'document_number') else '',
        })
    except Donor.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Донор не найден'})
