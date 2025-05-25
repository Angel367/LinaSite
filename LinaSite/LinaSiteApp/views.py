import json
from django.utils import timezone

from django.shortcuts import render

# Create your views here.

from .models import PaymentApplication

def auth(request):
    return render(request, 'auth.html')


def logout(request):
    request.session.flush()
    return redirect('/app/auth/')

def check_creds(request):
    creds = [
        {
            "role": "registrator",
            "name": "Регистратор",
            "username": "registrator",
            "password": "12345678"
        },
        {
            "role": "specialist_med_cart",
            "name": "Специалист по работе с медицинскими картами",
            "username": "specialist_med_cart",
            "password": "12345678"
        },
        {
            "role": "medical_sister",
            "name": "Медицинская сестра лаборатории",
            "username": "medical_sister",
            "password": "12345678"
        },
        {
            "role": "doctor",
            "name": "Врач-трансфузиолог",
            "username": "doctor",
            "password": "12345678"
        },
        {
            "role": "operational_medical_sister",
            "name": "Операционная медицинская сестра",
            "username": "operational_medical_sister",
            "password": "12345678"
        },
        {
            "role": "specialist_payment",
            "name": "Специалист по выплате мер социальной поддержки",
            "username": "specialist_payment",
            "password": "12345678"
        }
    ]
    parsed = json.loads(request.body.decode('utf-8'))
    login = parsed['login']
    password = parsed['password']
    for cred in creds:
        if cred['username'] == login and cred['password'] == password:
            # Устанавливаем куки для хранения информации о пользователе
            request.session['role'] = cred['role']
            request.session['role_descr'] = cred['name']
            return JsonResponse({
                'success': True,
                'role': cred['role'],
                'name': cred['name'],
            })
    return HttpResponse(status=401)

def index(request):
    """
    Основная страница приложения.
    """
    try:
        print(request.session['role'])
    except Exception as e:
        print(e)
        return redirect('/app/auth/')
    is_first_button = False
    if request.session['role'] == 'registrator' or request.session['role'] == 'specialist_med_cart':
        is_first_button = True
    return render(request, 'DonorInfo.html', {"is_first_button": is_first_button})


# views.py
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, FileResponse
from .models import Donor, BloodComponent, Donation, Payment, DirectionBase
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
import datetime


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
        for donor in queryset:  # Ограничиваем результат пятью записями
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
        is_first_donation = request.POST.get('is_first_donation') == 'on'
        donation_date = request.POST.get('donation_date')
        donation_type = request.POST.get('donation_type')
        payment_type = request.POST.get('payment_type')
        document_number = request.POST.get('document_number')
        documents_changed = request.POST.get('documents_changed') == 'on'
        donation_location = request.POST.get('donation_location')
        donation_address = request.POST.get('donation_address')
        contraindications = request.POST.get('contraindications')
        contraindication_details = request.POST.get('contraindication_details')
        directions_needed = request.POST.get('directions_needed')
        directions_details = request.POST.get('directions_details')
        snils = request.POST.get('snils')
        donor_address = request.POST.get('donor_address')

        # Парсинг компонентов
        components_data = request.POST.get('components', '[]')
        selected_component_types = []
        try:
            selected_component_types = json.loads(components_data)
        except json.JSONDecodeError:
            pass  # Обработка ошибки если JSON невалиден

        if is_first_donation:
            # Создание нового донора, если это первая донация
            new_donor = Donor.objects.create(
                snils=snils,
                last_name="Новый",  # Временные данные
                first_name="Донор",  # Временные данные
                blood_group="O+",  # Значение по умолчанию
                rh_factor="+",  # Значение по умолчанию
                kell_factor="-",  # Значение по умолчанию
                last_weight=0,  # Будет обновлено позже
                last_pressure="0/0",  # Будет обновлено позже
                document_number=document_number,
                registration_address=donor_address,
                fact_address=donor_address
            )
            donor = new_donor
        else:
            # Если это не первая донация, получаем выбранного донора
            donor_id = request.POST.get('donor')
            donor = get_object_or_404(Donor, id=donor_id)

            # Обновляем документы донора, если они изменились
            if documents_changed:
                donor.document_number = document_number
                donor.save()

        # Создаем донацию - убраны неподдерживаемые поля
        donation = Donation.objects.create(
            donor=donor,
            donation_date=donation_date,
            donation_type=donation_type,
            payment_type=payment_type,
            is_first_donation=is_first_donation,
            documents_changed=documents_changed,
            donation_location=donation_location,
            donation_address=donation_address,
            contraindications=contraindications,
            contraindication_details=contraindication_details,
            directions_needed=directions_needed,
            directions_details=directions_details
        )

        # Добавляем компоненты на основе их типов
        if selected_component_types:
            component_mapping = {
                'whole_blood': 'Цельная кровь',
                'plasma': 'Плазма',
                'platelets': 'Тромбоциты',
                'erythrocytes': 'Эритроциты',
                'granulocytes': 'Гранулоциты'
            }

            components_to_add = []
            for component_type in selected_component_types:
                component_name = component_mapping.get(component_type)
                if component_name:
                    component, _ = BloodComponent.objects.get_or_create(name=component_name)
                    components_to_add.append(component)

            if components_to_add:
                donation.components.set(components_to_add)

        # Увеличиваем количество донаций донора
        donor.donation_count = donor.donation_count + 1
        donor.save()

        return redirect('donor_search')  # Перенаправляем на список донаций

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


def payment_register(request):
    payment_to_edit = None
    edit_mode = False

    # Проверяем, режим редактирования или создания
    # Проверяем как GET, так и POST параметры
    edit_payment_id = None
    if 'edit' in request.GET:
        edit_payment_id = request.GET.get('edit')
    elif request.method == 'POST' and 'edit_payment_id' in request.POST:
        edit_payment_id = request.POST.get('edit_payment_id')

    if edit_payment_id:
        try:
            payment_to_edit = get_object_or_404(Payment, id=edit_payment_id)
            edit_mode = True
        except:
            pass

    # Проверяем права на редактирование
    try:
        current_user_role = request.session['role']
        is_can_edit = (current_user_role == "specialist_payment")
    except KeyError:
        is_can_edit = False

    # Если это редактирование и нет прав, перенаправляем на поиск
    if edit_mode and not is_can_edit:
        return redirect('payment_search')

    if request.method == 'POST':
        # Обработка формы
        donation_id = request.POST.get('donation')
        donor_id = request.POST.get('donor')
        document_id = request.POST.get('document_id')
        payment_components_data = request.POST.get('payment_components', '[]')
        is_accumulative = request.POST.get('accumulative_system') == 'on'
        is_paid_donation = request.POST.get('is_paid_donation') == 'on'
        food_compensation = request.POST.get('food_compensation') == 'on'
        payment_type = request.POST.get('payment_type', '')
        amount = request.POST.get('amount')

        # Получаем объекты
        donation = get_object_or_404(Donation, id=donation_id)
        donor = get_object_or_404(Donor, id=donor_id)

        # Устанавливаем метод выплаты
        payment_method = 'accumulative' if is_accumulative else 'standard'

        # Создаем запись о выплате или обновляем существующую
        if edit_mode and payment_to_edit:
            # Обновляем существующую запись
            payment_to_edit.donation = donation
            payment_to_edit.donor = donor
            payment_to_edit.payment_method = payment_method
            payment_to_edit.is_paid_donation = is_paid_donation
            payment_to_edit.food_compensation = food_compensation
            payment_to_edit.amount = amount
            payment_to_edit.document_id = document_id
            payment_to_edit.payment_type = payment_type
            payment_to_edit.save()
            payment = payment_to_edit
        else:
            # Создаем новую запись
            payment = Payment.objects.create(
                donation=donation,
                donor=donor,
                payment_date=datetime.date.today(),
                expiration_date=donation.donation_date + datetime.timedelta(days=1),
                payment_method=payment_method,
                is_paid_donation=is_paid_donation,
                food_compensation=food_compensation,
                amount=amount,
                document_id=document_id,
                payment_type=payment_type,
                is_payment_processed=False
            )

        # Обработка компонентов из JSON
        try:
            selected_components = json.loads(payment_components_data)
            # Здесь можно сохранить связи с компонентами, если нужно
        except json.JSONDecodeError:
            pass

        # Обработка загрузки файла заявления, если есть
        application_file = request.FILES.get('application_file')
        if application_file and not edit_mode:  # Добавляем заявление только при создании
            PaymentApplication.objects.create(
                payment=payment,
                file=application_file
            )

        return redirect('payment_search')  # Перенаправляем на поиск выплат

    # Для GET-запроса отображаем форму
    donations = Donation.objects.all().order_by('-donation_date')
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    context = {
        'donations': donations,
        'donors': donors,
        'edit_mode': edit_mode,
        'is_can_edit': is_can_edit,
    }

    # Если это редактирование, добавляем данные для заполнения формы
    if edit_mode and payment_to_edit:
        context['payment'] = payment_to_edit

        # Получаем компоненты для редактирования
        components = []
        for component in payment_to_edit.donation.components.all():
            if component.name == "Цельная кровь":
                components.append("whole_blood")
            elif component.name == "Плазма":
                components.append("plasma")
            elif component.name == "Тромбоциты":
                components.append("platelets")
            elif component.name == "Эритроциты":
                components.append("erythrocytes")
            elif component.name == "Гранулоциты":
                components.append("granulocytes")

        context['selected_components'] = json.dumps(components)

    return render(request, 'payment_register.html', context)


def get_donation_info(request, donation_id):
    """API для получения информации о донации"""
    try:
        donation = Donation.objects.get(id=donation_id)

        # Получаем компоненты крови
        components = []
        for component in donation.components.all():
            # Маппинг имен на коды для фронтенда
            if component.name == "Цельная кровь":
                components.append("whole_blood")
            elif component.name == "Плазма":
                components.append("plasma")
            elif component.name == "Тромбоциты":
                components.append("platelets")
            elif component.name == "Эритроциты":
                components.append("erythrocytes")
            elif component.name == "Гранулоциты":
                components.append("granulocytes")

        return JsonResponse({
            'success': True,
            'donor_id': donation.donor.id,
            'donation_date': donation.donation_date.strftime('%Y-%m-%d'),
            'donation_type': donation.donation_type,
            'payment_type': donation.payment_type,
            'components': components,
        })
    except Donation.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Донация не найдена'})


def payment_search(request):
    # Параметр для отслеживания, был ли выполнен поиск
    search_performed = any(key for key in request.GET if key != 'csrfmiddlewaretoken')

    # Получаем параметры фильтрации из GET-запроса
    donor_id = request.GET.get('donor', '')
    date_str = request.GET.get('date', '')
    payment_type = request.GET.get('payment_type', 'any')
    document_type = request.GET.get('document_type', '')

    # Инициализируем базовые queryset
    payments = Payment.objects.all().select_related('donor', 'donation').order_by('-payment_date')

    # Применяем общие фильтры
    if donor_id:
        payments = payments.filter(donor_id=donor_id)

    if date_str:
        try:
            date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            payments = payments.filter(
                Q(payment_date=date_obj) |
                Q(expiration_date=date_obj)
            )
        except ValueError:
            pass

    if payment_type and payment_type != 'any':
        payments = payments.filter(payment_type=payment_type)

    # Создаем список результатов для отображения
    display_results = []

    # Если нужно показать сведения о выплате или все документы
    if document_type == '' or document_type == 'payment_info':
        for payment in payments:
            # Добавляем сведения о выплате
            display_results.append({
                'id': payment.id,
                'donor_name': payment.donor.get_full_name(),
                'donor_lastname': payment.donor.last_name,
                'donor_firstname': payment.donor.first_name,
                'amount': payment.amount,
                'donation_date': payment.donation.donation_date,
                'document_id': payment.document_id,
                'payment_type': payment.payment_type,
                'payment_type_display': payment.get_payment_type_display(),
                'payment_date': payment.payment_date,
                'expiration_date': payment.expiration_date,
                'is_application': False,
                'payment_id': payment.id
            })

    # Если нужно показать заявления на выплату или все документы
    if document_type == '' or document_type == 'payment_application':
        # Получаем заявления
        applications = PaymentApplication.objects.filter(
            payment__in=payments
        ).select_related('payment', 'payment__donor', 'payment__donation')

        for app in applications:
            # Добавляем заявления
            display_results.append({
                'id': app.id,
                'donor_name': app.payment.donor.get_full_name(),
                'donor_lastname': app.payment.donor.last_name,
                'donor_firstname': app.payment.donor.first_name,
                'amount': app.payment.amount,
                'donation_date': app.payment.donation.donation_date,
                'document_id': app.payment.document_id,
                'payment_type': app.payment.payment_type,
                'payment_type_display': app.payment.get_payment_type_display(),
                'payment_date': app.payment.payment_date,
                'expiration_date': app.payment.expiration_date,
                'is_application': True,
                'payment_id': app.payment.id,
                'application_id': app.id
            })

    # Сортировка результатов по дате выплаты (сначала новые)
    display_results.sort(key=lambda x: x['payment_date'], reverse=True)

    # Получаем списки для фильтров
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    payment_dates = Payment.objects.values_list('payment_date', flat=True).distinct().order_by('-payment_date')
    expiration_dates = Payment.objects.values_list('expiration_date', flat=True).distinct().order_by('-expiration_date')

    # Объединяем даты выплат и истечения
    all_dates = list(payment_dates) + list(expiration_dates)
    unique_dates = sorted(set(date for date in all_dates if date is not None), reverse=True)

    return render(request, 'payment_search.html', {
        'results': display_results,
        'donors': donors,
        'dates': unique_dates,
        'selected_donor': donor_id,
        'selected_date': date_str,
        'selected_payment_type': payment_type,
        'selected_document_type': document_type,
        'search_performed': search_performed,
    })


def payment_details(request, payment_id):
    """Страница с детальной информацией о выплате"""
    payment = get_object_or_404(Payment, id=payment_id)

    # Проверяем права на редактирование
    try:
        current_user_role = request.session['role']
        is_can_edit = (current_user_role == "specialist_payment")
    except KeyError:
        is_can_edit = False

    # Получаем прикрепленные заявления, если есть
    applications = PaymentApplication.objects.filter(payment=payment).order_by('-upload_date')

    return render(request, 'payment_details.html', {
        'payment': payment,
        'is_can_edit': is_can_edit,
        'applications': applications,
    })


def get_payment_info(request, payment_id):
    """API для получения информации о выплате"""
    try:
        payment = Payment.objects.select_related('donor', 'donation').get(id=payment_id)

        return JsonResponse({
            'success': True,
            'id': payment.id,
            'donor_name': payment.donor.get_full_name(),
            'donor_id': payment.donor.id,
            'payment_date': payment.payment_date.strftime('%d.%m.%Y'),
            'expiration_date': payment.expiration_date.strftime('%d.%m.%Y') if payment.expiration_date else None,
            'amount': float(payment.amount),
            'payment_type': payment.payment_type,
            'payment_type_display': payment.get_payment_type_display(),
            'document_id': payment.document_id,
            'document_type': payment.document_type,
            'donation_date': payment.donation.donation_date.strftime('%d.%m.%Y'),
            'is_paid_donation': payment.is_paid_donation,
            'food_compensation': payment.food_compensation,
        })
    except Payment.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Выплата не найдена'})


def upload_payment_application(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id)

    # Проверяем права на редактирование
    try:
        current_user_role = request.session['role']
        is_can_edit = (current_user_role == "specialist_payment")
    except KeyError:
        is_can_edit = False

    if not is_can_edit:
        return redirect('payment_details', payment_id=payment_id)

    if request.method == 'POST':
        application_file = request.FILES.get('application_file')

        if application_file:
            PaymentApplication.objects.create(
                payment=payment,
                file=application_file
            )

            return redirect('payment_details', payment_id=payment_id)

    return render(request, 'upload_application.html', {
        'payment': payment
    })


from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Donor, Donation

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Donor, Donation, DonationDirection
import datetime


def index_direction(request):
    """
    Меню направления.
    """
    link = ""
    is_first_button = True
    try:
        current_user_role = request.session['role']
    except KeyError:
        return render(request, 'direction_menu.html', {"is_first_button": False})
    if current_user_role == "operational_medical_sister":
        link = '/app/donation-direction/create/'
    elif current_user_role == "doctor":
        link = "/app/examination-direction/create/"
    elif current_user_role == "medical_sister":
        link = "/app/blood-analysis-direction/create/"
    else:
        is_first_button = False

    return render(request, 'direction_menu.html', {"link": link, "is_first_button": is_first_button})


def index_donation(request):
    """
    Меню донации.
    """
    print(request.session['role'])
    is_first_button = False
    if request.session['role'] == 'registrator':
        is_first_button = True
    return render(request, 'donation_menu.html', {"is_first_button": is_first_button})


def index_payment(request):
    """
    Меню донации.
    """
    print(request.session['role'])
    is_first_button = False
    if request.session['role'] == 'specialist_payment':
        is_first_button = True
    return render(request, 'payment_menu.html', {"is_first_button": is_first_button})


def donation_direction_form(request):
    """View to display the donation direction form"""
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    # Generate some available dates (next 7 days)
    today = datetime.date.today()
    available_dates = [today + datetime.timedelta(days=i) for i in range(31)]

    context = {
        'donors': donors,
        'available_dates': available_dates,
    }
    return render(request, 'direction_donation.html', context)


@require_http_methods(["POST"])
def donation_direction_create(request):
    """View to handle the form submission"""
    try:
        donor_id = request.POST.get('donor')
        direction_date = request.POST.get('direction_date')
        blood_group = request.POST.get('blood_group')
        rh_factor = request.POST.get('rh_factor')
        document_number = request.POST.get('document_number')
        donation_number = request.POST.get('donation_number')
        previous_donation_number = request.POST.get('previous_donation_number')
        previous_donation_date = request.POST.get('previous_donation_date')
        donation_type = request.POST.get('donation_type')

        # Create the donation direction
        donor = Donor.objects.get(id=donor_id)
        direction = DonationDirection(
            donor=donor,
            direction_date=direction_date,
            blood_group=blood_group,
            rh_factor=rh_factor,
            document_number=document_number,
            donation_number=donation_number,
            previous_donation_number=previous_donation_number,
            donation_type=donation_type
        )

        # Handle the previous donation date if provided
        if previous_donation_date:
            direction.previous_donation_date = previous_donation_date

        direction.save()

        # Redirect to a success page or listing
        return redirect('donation_direction_list')
    except Exception as e:
        # Handle errors
        return render(request, 'direction_donation.html', {
            'error_message': str(e),
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': [datetime.date.today() + datetime.timedelta(days=i) for i in range(31)],
        })


@require_http_methods(["GET"])
def donor_api(request, donor_id):
    """API endpoint to get donor information"""
    try:
        donor = Donor.objects.get(id=donor_id)
        return JsonResponse({
            'success': True,
            'document_number': donor.document_number,
            'blood_group': donor.blood_group,
            'rh_factor': donor.rh_factor,
        })
    except Donor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Донор не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


@require_http_methods(["GET"])
def donor_last_donation_api(request, donor_id):
    """API endpoint to get donor's last donation"""
    try:
        donor = Donor.objects.get(id=donor_id)
        last_donation = Donation.objects.filter(donor=donor).order_by('-donation_date').first()

        if last_donation:
            return JsonResponse({
                'success': True,
                'last_donation': {
                    'donation_number': last_donation.id,  # Using ID as donation number
                    'donation_date': last_donation.donation_date.strftime('%Y-%m-%d')
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'last_donation': None
            })
    except Donor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Донор не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Donor, ExaminationDirection
import datetime


def examination_direction_form(request):
    """View to display the examination direction form"""
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    # Generate some available dates (next 7 days)
    today = datetime.date.today()
    available_dates = [today + datetime.timedelta(days=i) for i in range(31)]

    context = {
        'donors': donors,
        'available_dates': available_dates,
    }
    return render(request, 'examination_direction_form.html', context)


@require_http_methods(["POST"])
def examination_direction_create(request):
    """View to handle the form submission"""
    try:
        donor_id = request.POST.get('donor')
        planned_donation_date_str = request.POST.get('planned_donation_date')
        planned_donation_date = datetime.datetime.strptime(planned_donation_date_str, '%Y-%m-%d').date()

        document_number = request.POST.get('document_number')
        blood_group = request.POST.get('blood_group')
        rh_factor = request.POST.get('rh_factor')
        donation_type = request.POST.get('donation_type')

        # Medical examination fields
        has_complaints = request.POST.get('has_complaints')
        has_contraindications = request.POST.get('has_contraindications')
        normal_mucous = request.POST.get('normal_mucous')
        clean_skin = request.POST.get('clean_skin')
        normal_cardiac = request.POST.get('normal_cardiac')
        normal_abdomen = request.POST.get('normal_abdomen')
        recent_operations = request.POST.get('recent_operations')

        # Vital signs
        blood_pressure = request.POST.get('blood_pressure')
        pulse = request.POST.get('pulse')
        temperature = request.POST.get('temperature')
        height = request.POST.get('height')
        weight = request.POST.get('weight')

        # Approve/Reject
        is_approved = request.POST.get('is_approved') == 'true'

        # Create the examination direction
        donor = Donor.objects.get(id=donor_id)
        examination = ExaminationDirection(
            donor=donor,
            planned_donation_date=planned_donation_date,
            document_number=document_number,
            blood_group=blood_group,
            rh_factor=rh_factor,
            donation_type=donation_type,
            has_complaints=has_complaints,
            has_contraindications=has_contraindications,
            normal_mucous=normal_mucous,
            clean_skin=clean_skin,
            normal_cardiac=normal_cardiac,
            normal_abdomen=normal_abdomen,
            recent_operations=recent_operations,
            blood_pressure=blood_pressure,
            pulse=pulse,
            temperature=temperature,
            height=height,
            weight=weight,
            is_approved=is_approved
        )
        examination.save()

        # Update donor's last known measurements
        donor.last_weight = weight
        donor.last_pressure = blood_pressure
        donor.save()

        # Redirect to a success page or listing
        return redirect('examination_direction_list')
    except Exception as e:
        # Handle errors
        return render(request, 'examination_direction_form.html', {
            'error_message': str(e),
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': [datetime.date.today() + datetime.timedelta(days=i) for i in range(31)],
        })


@require_http_methods(["GET"])
def donor_api(request, donor_id):
    """API endpoint to get donor information"""
    try:
        donor = Donor.objects.get(id=donor_id)

        # Get the donor's preferred donation type based on history
        preferred_donation_type = None
        last_donation = donor.donations.order_by('-donation_date').first()
        if last_donation:
            preferred_donation_type = last_donation.donation_type

        return JsonResponse({
            'success': True,
            'document_number': donor.document_number,
            'blood_group': donor.blood_group,
            'rh_factor': donor.rh_factor,
            'kell_factor': donor.kell_factor,  # Added Kell factor
            'last_weight': donor.last_weight,
            'last_pressure': donor.last_pressure,
            'last_height': donor.height if hasattr(donor, 'height') else None,
            'preferred_donation_type': preferred_donation_type
        })
    except Donor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Донор не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Donor, BloodAnalysisDirection
import datetime


def blood_analysis_direction_detail(request, pk):
    """View to display the blood analysis direction details"""
    try:
        direction = BloodAnalysisDirection.objects.get(pk=pk)
        donors = Donor.objects.all().order_by('last_name', 'first_name')

        # Generate some available dates (next 31 days)
        today = datetime.date.today()
        available_dates = [today + datetime.timedelta(days=i) for i in range(31)]

        # Проверка, может ли пользователь редактировать направление
        try:
            current_user_role = request.session['role']
        except KeyError:
            return render(request, 'direction_menu.html', {"is_first_button": False})

        if current_user_role == 'medical_sister':
            can_edit = True
        else:
            can_edit = False

        context = {
            'direction': direction,
            'donors': donors,
            'available_dates': available_dates,
            'read_only': True,
            'can_edit': can_edit
        }
        return render(request, 'blood_analysis_direction.html', context)
    except BloodAnalysisDirection.DoesNotExist:
        return redirect('direction_search')


def blood_analysis_direction_edit(request, pk):
    """View to edit the blood analysis direction"""
    try:
        direction = BloodAnalysisDirection.objects.get(pk=pk)
        donors = Donor.objects.all().order_by('last_name', 'first_name')

        # Generate some available dates (next 31 days)
        today = datetime.date.today()
        available_dates = [today + datetime.timedelta(days=i) for i in range(31)]

        context = {
            'direction': direction,
            'donors': donors,
            'available_dates': available_dates,
            'edit_mode': True
        }
        return render(request, 'blood_analysis_direction.html', context)
    except BloodAnalysisDirection.DoesNotExist:
        return redirect('direction_search')


@require_http_methods(["POST"])
def blood_analysis_direction_update(request, pk):
    """View to handle the update form submission"""
    try:
        direction = BloodAnalysisDirection.objects.get(pk=pk)

        # Обновление полей
        donor_id = request.POST.get('donor')
        planned_donation_date_str = request.POST.get('planned_donation_date')
        planned_donation_date = datetime.datetime.strptime(planned_donation_date_str, '%Y-%m-%d').date()
        document_number = request.POST.get('document_number')
        blood_group = request.POST.get('blood_group')
        rh_factor = request.POST.get('rh_factor')
        kell_factor = request.POST.get('kell_factor')
        donation_type = request.POST.get('donation_type')

        # Blood analysis parameters
        hemoglobin = request.POST.get('hemoglobin')
        erythrocytes_count = request.POST.get('erythrocytes_count')
        platelets_count = request.POST.get('platelets_count')
        leukocytes_count = request.POST.get('leukocytes_count')
        albumin = request.POST.get('albumin')
        globulin = request.POST.get('globulin')

        # Additional parameters
        soe = request.POST.get('soe')
        hct = request.POST.get('hct')
        mcv = request.POST.get('mcv')
        mch = request.POST.get('mch')
        mchc = request.POST.get('mchc')

        # Update the blood analysis direction
        donor = Donor.objects.get(id=donor_id)

        direction.donor = donor
        direction.planned_donation_date = planned_donation_date
        direction.document_number = document_number
        direction.blood_group = blood_group
        direction.rh_factor = rh_factor
        direction.kell_factor = kell_factor
        direction.donation_type = donation_type
        direction.hemoglobin = hemoglobin if hemoglobin else None
        direction.erythrocytes_count = erythrocytes_count if erythrocytes_count else None
        direction.platelets_count = platelets_count if platelets_count else None
        direction.leukocytes_count = leukocytes_count if leukocytes_count else None
        direction.albumin = albumin if albumin else None
        direction.globulin = globulin if globulin else None
        direction.soe = soe if soe else None
        direction.hct = hct if hct else None
        direction.mcv = mcv if mcv else None
        direction.mch = mch if mch else None
        direction.mchc = mchc if mchc else None

        direction.save()

        # Redirect to the detail view
        return redirect('blood_analysis_direction_detail', pk=direction.pk)
    except Exception as e:
        # Handle errors
        return render(request, 'blood_analysis_direction.html', {
            'error_message': str(e),
            'direction': direction,
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': [datetime.date.today() + datetime.timedelta(days=i) for i in range(31)],
            'edit_mode': True
        })


def blood_analysis_direction_form(request):
    """View to display the blood analysis direction form"""
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    # Generate some available dates (next 7 days)
    today = datetime.date.today()
    available_dates = [today + datetime.timedelta(days=i) for i in range(31)]

    context = {
        'donors': donors,
        'available_dates': available_dates,
    }
    return render(request, 'blood_analysis_direction.html', context)


@require_http_methods(["POST"])
def blood_analysis_direction_create(request):
    """View to handle the form submission"""
    try:
        donor_id = request.POST.get('donor')
        planned_donation_date_str = request.POST.get('planned_donation_date')
        planned_donation_date = datetime.datetime.strptime(planned_donation_date_str, '%Y-%m-%d').date()
        document_number = request.POST.get('document_number')
        blood_group = request.POST.get('blood_group')
        rh_factor = request.POST.get('rh_factor')
        kell_factor = request.POST.get('kell_factor')
        donation_type = request.POST.get('donation_type')

        # Blood analysis parameters
        hemoglobin = request.POST.get('hemoglobin')
        erythrocytes_count = request.POST.get('erythrocytes_count')
        platelets_count = request.POST.get('platelets_count')
        leukocytes_count = request.POST.get('leukocytes_count')
        albumin = request.POST.get('albumin')
        globulin = request.POST.get('globulin')

        # Additional parameters
        soe = request.POST.get('soe')
        hct = request.POST.get('hct')
        mcv = request.POST.get('mcv')
        mch = request.POST.get('mch')
        mchc = request.POST.get('mchc')

        # Create the blood analysis direction
        donor = Donor.objects.get(id=donor_id)
        blood_analysis = BloodAnalysisDirection(
            donor=donor,
            planned_donation_date=planned_donation_date,
            document_number=document_number,
            blood_group=blood_group,
            rh_factor=rh_factor,
            kell_factor=kell_factor,
            donation_type=donation_type,
            hemoglobin=hemoglobin if hemoglobin else None,
            erythrocytes_count=erythrocytes_count if erythrocytes_count else None,
            platelets_count=platelets_count if platelets_count else None,
            leukocytes_count=leukocytes_count if leukocytes_count else None,
            albumin=albumin if albumin else None,
            globulin=globulin if globulin else None,
            soe=soe if soe else None,
            hct=hct if hct else None,
            mcv=mcv if mcv else None,
            mch=mch if mch else None,
            mchc=mchc if mchc else None
        )
        blood_analysis.save()

        # Redirect to a success page or listing
        return redirect('/app/directions')
    except Exception as e:
        # Handle errors
        return render(request, 'blood_analysis_direction.html', {
            'error_message': str(e),
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': [datetime.date.today() + datetime.timedelta(days=i) for i in range(31)],
        })


@require_http_methods(["GET"])
def donor_last_blood_analysis_api(request, donor_id):
    """API endpoint to get donor's last blood analysis"""
    try:
        donor = Donor.objects.get(id=donor_id)
        last_analysis = BloodAnalysisDirection.objects.filter(donor=donor).order_by('-created_at').first()

        if last_analysis:
            return JsonResponse({
                'success': True,
                'last_analysis': {
                    'hemoglobin': float(last_analysis.hemoglobin) if last_analysis.hemoglobin else None,
                    'erythrocytes_count': float(
                        last_analysis.erythrocytes_count) if last_analysis.erythrocytes_count else None,
                    'platelets_count': float(last_analysis.platelets_count) if last_analysis.platelets_count else None,
                    'leukocytes_count': float(
                        last_analysis.leukocytes_count) if last_analysis.leukocytes_count else None,
                    'albumin': float(last_analysis.albumin) if last_analysis.albumin else None,
                    'globulin': float(last_analysis.globulin) if last_analysis.globulin else None,
                    'soe': float(last_analysis.soe) if last_analysis.soe else None,
                    'hct': float(last_analysis.hct) if last_analysis.hct else None,
                    'mcv': float(last_analysis.mcv) if last_analysis.mcv else None,
                    'mch': float(last_analysis.mch) if last_analysis.mch else None,
                    'mchc': float(last_analysis.mchc) if last_analysis.mchc else None
                }
            })
        else:
            return JsonResponse({
                'success': True,
                'last_analysis': None
            })
    except Donor.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Донор не найден'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        })


def direction_search(request):
    """View for searching and listing directions"""
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    # Get filter parameters
    donor_id = request.GET.get('donor', '')
    date_filter = request.GET.get('date', '')
    status_filter = request.GET.get('status', '')
    direction_location = request.GET.get('direction_location', 'any')
    direction_type = request.GET.get('direction_type', 'any')

    # Start with all directions
    directions = DirectionBase.objects.all()

    # Apply filters
    if donor_id:
        directions = directions.filter(donor_id=donor_id)

    if date_filter:

        today = timezone.now().date()
        if date_filter == 'today':
            directions = directions.filter(created_at__date=today)
        elif date_filter == 'week':
            week_ago = today - datetime.timedelta(days=7)
            directions = directions.filter(created_at__date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - datetime.timedelta(days=30)
            directions = directions.filter(created_at__date__gte=month_ago)
        elif date_filter == 'year':
            year_ago = today - datetime.timedelta(days=365)
            directions = directions.filter(created_at__date__gte=year_ago)

    if status_filter:
        if status_filter == 'active':
            directions = directions.filter(is_completed=False, expiry_date__gte=timezone.now().date())
        elif status_filter == 'expired':
            directions = directions.filter(is_completed=False, expiry_date__lt=timezone.now().date())
        elif status_filter == 'completed':
            directions = directions.filter(is_completed=True)

    if direction_location != 'any':
        directions = directions.filter(location=direction_location)

    if direction_type != 'any':
        directions = directions.filter(type=direction_type)

    context = {
        'donors': donors,
        'directions': directions,
        'selected_donor': donor_id,
        'selected_date': date_filter,
        'selected_status': status_filter,
        'selected_location': direction_location,
        'selected_type': direction_type,
    }

    return render(request, 'direction_search.html', context)


def get_available_donation_dates():
    # Создаем список дат, начиная с текущей даты и на 30 дней вперед
    today = timezone.now().date()
    return [today + timezone.timedelta(days=i) for i in range(31)]


def donation_direction_view(request, direction_id):
    """View a donation direction in read-only mode"""
    direction = get_object_or_404(DonationDirection, id=direction_id)

    # Получаем список доноров для селекта (даже если он не будет использоваться)
    donors = Donor.objects.all()

    # Получаем доступные даты для селекта (хотя они также не будут использоваться в read-only режиме)
    available_dates = get_available_donation_dates()  # это функция, которая должна возвращать доступные даты

    # Проверка, может ли пользователь редактировать направление
    try:
        current_user_role = request.session['role']
    except KeyError:
        return render(request, 'direction_menu.html', {"is_first_button": False})

    if current_user_role == 'operational_medical_sister':
        can_edit = True
    else:
        can_edit = False


    context = {
        'direction': direction,
        'donors': donors,
        'available_dates': available_dates,
        'read_only': True,  # This flag will be used in the template to make fields read-only
        'can_edit': can_edit
    }

    return render(request, 'direction_donation.html', context)


def donation_direction_edit(request, direction_id):
    """View to edit a donation direction"""
    try:
        direction = DonationDirection.objects.get(id=direction_id)
        donors = Donor.objects.all().order_by('last_name', 'first_name')

        # Generate some available dates (next 31 days)
        today = datetime.date.today()
        available_dates = [today + datetime.timedelta(days=i) for i in range(31)]

        context = {
            'direction': direction,
            'donors': donors,
            'available_dates': available_dates,
            'edit_mode': True
        }
        return render(request, 'direction_donation.html', context)
    except DonationDirection.DoesNotExist:
        return redirect('direction_search')


@require_http_methods(["POST"])
def donation_direction_update(request, direction_id):
    """View to handle the update form submission"""
    try:
        direction = DonationDirection.objects.get(id=direction_id)

        # Update fields
        donor_id = request.POST.get('donor')
        direction_date = request.POST.get('direction_date')
        blood_group = request.POST.get('blood_group')
        rh_factor = request.POST.get('rh_factor')
        document_number = request.POST.get('document_number')
        donation_number = request.POST.get('donation_number')
        previous_donation_number = request.POST.get('previous_donation_number')
        previous_donation_date = request.POST.get('previous_donation_date')
        donation_type = request.POST.get('donation_type')

        # Update the donation direction
        donor = Donor.objects.get(id=donor_id)

        direction.donor = donor
        direction.direction_date = direction_date
        direction.blood_group = blood_group
        direction.rh_factor = rh_factor
        direction.document_number = document_number
        direction.donation_number = donation_number
        direction.previous_donation_number = previous_donation_number
        direction.donation_type = donation_type

        # Handle the previous donation date if provided
        if previous_donation_date:
            direction.previous_donation_date = previous_donation_date
        else:
            direction.previous_donation_date = None

        direction.save()

        # Redirect to the view page
        return redirect('donation_direction_view', direction_id=direction.id)
    except Exception as e:
        # Handle errors
        return render(request, 'direction_donation.html', {
            'error_message': str(e),
            'direction': direction,
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': [datetime.date.today() + datetime.timedelta(days=i) for i in range(31)],
            'edit_mode': True
        })


def examination_direction_view(request, direction_id):
    """View an examination direction in read-only mode"""
    direction = get_object_or_404(ExaminationDirection, id=direction_id)

    # Получаем список доноров для селекта (даже если он не будет использоваться)
    donors = Donor.objects.all()

    # Получаем доступные даты для селекта (хотя они также не будут использоваться в read-only режиме)
    available_dates = get_available_donation_dates()  # это функция, которая должна возвращать доступные даты

    # Проверка, может ли пользователь редактировать направление
    try:
        current_user_role = request.session['role']
    except KeyError:
        return render(request, 'direction_menu.html', {"is_first_button": False})

    if current_user_role == 'doctor':
        can_edit = True
    else:
        can_edit = False

    context = {
        'direction': direction,
        'donors': donors,
        'available_dates': available_dates,
        'read_only': True,  # This flag will be used in the template to make fields read-only
        'can_edit': can_edit
    }

    return render(request, 'examination_direction_form.html', context)


def examination_direction_edit(request, direction_id):
    """View to edit an examination direction"""
    try:
        direction = ExaminationDirection.objects.get(id=direction_id)
        donors = Donor.objects.all().order_by('last_name', 'first_name')

        # Generate some available dates (next 31 days)
        today = datetime.date.today()
        available_dates = [today + datetime.timedelta(days=i) for i in range(31)]

        context = {
            'direction': direction,
            'donors': donors,
            'available_dates': available_dates,
            'edit_mode': True
        }
        return render(request, 'examination_direction_form.html', context)
    except ExaminationDirection.DoesNotExist:
        return redirect('direction_search')


@require_http_methods(["POST"])
def examination_direction_update(request, direction_id):
    """View to handle the update form submission"""
    try:
        direction = ExaminationDirection.objects.get(id=direction_id)

        # Update fields
        donor_id = request.POST.get('donor')
        planned_donation_date_str = request.POST.get('planned_donation_date')
        planned_donation_date = datetime.datetime.strptime(planned_donation_date_str, '%Y-%m-%d').date()

        document_number = request.POST.get('document_number')
        blood_group = request.POST.get('blood_group')
        rh_factor = request.POST.get('rh_factor')
        donation_type = request.POST.get('donation_type')

        # Medical examination fields
        has_complaints = request.POST.get('has_complaints')
        has_contraindications = request.POST.get('has_contraindications')
        normal_mucous = request.POST.get('normal_mucous')
        clean_skin = request.POST.get('clean_skin')
        normal_cardiac = request.POST.get('normal_cardiac')
        normal_abdomen = request.POST.get('normal_abdomen')
        recent_operations = request.POST.get('recent_operations')

        # Vital signs
        blood_pressure = request.POST.get('blood_pressure')
        pulse = request.POST.get('pulse')
        temperature = request.POST.get('temperature')
        height = request.POST.get('height')
        weight = request.POST.get('weight')

        # Approve/Reject
        is_approved = request.POST.get('is_approved') == 'true'

        # Update examination direction
        donor = Donor.objects.get(id=donor_id)

        direction.donor = donor
        direction.planned_donation_date = planned_donation_date
        direction.document_number = document_number
        direction.blood_group = blood_group
        direction.rh_factor = rh_factor
        direction.donation_type = donation_type
        direction.has_complaints = has_complaints
        direction.has_contraindications = has_contraindications
        direction.normal_mucous = normal_mucous
        direction.clean_skin = clean_skin
        direction.normal_cardiac = normal_cardiac
        direction.normal_abdomen = normal_abdomen
        direction.recent_operations = recent_operations
        direction.blood_pressure = blood_pressure
        direction.pulse = pulse
        direction.temperature = temperature
        direction.height = height
        direction.weight = weight
        direction.is_approved = is_approved

        direction.save()

        # Update donor's last known measurements
        donor.last_weight = weight
        donor.last_pressure = blood_pressure
        donor.save()

        # Redirect to the view page
        return redirect('examination_direction_view', direction_id=direction.id)
    except Exception as e:
        # Handle errors
        return render(request, 'examination_direction_form.html', {
            'error_message': str(e),
            'direction': direction,
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': [datetime.date.today() + datetime.timedelta(days=i) for i in range(31)],
            'edit_mode': True
        })


def blood_analysis_direction_view(request, direction_id):
    """View a blood analysis direction in read-only mode"""
    direction = get_object_or_404(BloodAnalysisDirection, id=direction_id)

    # Получаем список доноров для селекта (даже если он не будет использоваться)
    donors = Donor.objects.all()

    # Получаем доступные даты для селекта (хотя они также не будут использоваться в read-only режиме)
    available_dates = get_available_donation_dates()  # это функция, которая должна возвращать доступные даты

    context = {
        'direction': direction,
        'donors': donors,
        'available_dates': available_dates,
        'read_only': True  # This flag will be used in the template to make fields read-only
    }

    return render(request, 'blood_analysis_direction.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Donor, ExternalDirection
import datetime


def external_direction_edit(request, direction_id):
    """View to edit an external direction"""
    try:
        direction = ExternalDirection.objects.get(id=direction_id)
        donors = Donor.objects.all().order_by('last_name', 'first_name')

        # Generate dates for dropdown selections with expanded range to ensure original dates are included
        today = datetime.date.today()

        # Get min date to ensure we cover original dates
        min_date = min(today, direction.issue_date, direction.start_date) - datetime.timedelta(days=30)

        # Generate dates for issue_date and start_date (60 days from min_date)
        available_dates = [min_date + datetime.timedelta(days=i) for i in range(60)]

        # Generate dates for end_date (180 days from min_date)
        expiry_dates = [min_date + datetime.timedelta(days=i) for i in range(180)]

        context = {
            'direction': direction,
            'donors': donors,
            'available_dates': available_dates,
            'expiry_dates': expiry_dates,
            'edit_mode': True
        }
        return render(request, 'external_direction_form.html', context)
    except ExternalDirection.DoesNotExist:
        return redirect('direction_search')


@require_http_methods(["POST"])
def external_direction_update(request, direction_id):
    """View to handle the update form submission"""
    try:
        direction = ExternalDirection.objects.get(id=direction_id)

        # Update fields
        donor_id = request.POST.get('donor')
        issue_date = request.POST.get('issue_date')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        research_type = request.POST.get('research_type')
        clinic_address = request.POST.get('clinic_address')
        issue_reason = request.POST.get('issue_reason')

        # Update the external direction
        donor = Donor.objects.get(id=donor_id)

        direction.donor = donor
        direction.issue_date = issue_date
        direction.start_date = start_date
        direction.end_date = end_date
        direction.research_type = research_type
        direction.clinic_address = clinic_address
        direction.issue_reason = issue_reason

        direction.save()

        # Update the expiry date in the DirectionBase model
        base_direction = direction.base_direction.first()
        if base_direction:
            base_direction.expiry_date = end_date
            base_direction.save()

        # Redirect to the view page
        return redirect('external_direction_view', direction_id=direction.id)
    except Exception as e:
        # Handle errors
        donors = Donor.objects.all().order_by('last_name', 'first_name')
        today = datetime.date.today()
        available_dates = [today + datetime.timedelta(days=i) for i in range(30)]
        expiry_dates = [today + datetime.timedelta(days=i) for i in range(180)]

        return render(request, 'external_direction_form.html', {
            'error_message': str(e),
            'direction': direction,
            'donors': donors,
            'available_dates': available_dates,
            'expiry_dates': expiry_dates,
            'edit_mode': True
        })


def external_direction_form(request, donor_id=None):
    """View to display the external direction form"""
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    if donor_id:
        donor = donors.get(id=donor_id)
    else:
        donor = None
    # Generate dates for the next 30 days for issue date and start date
    today = datetime.date.today()
    available_dates = [today + datetime.timedelta(days=i) for i in range(30)]

    # Generate dates for the next 6 months for end date
    expiry_dates = [today + datetime.timedelta(days=i) for i in range(180)]

    context = {
        'donors': donors,
        'donor_pre_inf': donor,
        'available_dates': available_dates,
        'expiry_dates': expiry_dates,
    }
    return render(request, 'external_direction_form.html', context)


@require_http_methods(["POST"])
def external_direction_create(request):
    """View to handle the form submission"""
    try:
        donor_id = request.POST.get('donor')
        issue_date = request.POST.get('issue_date')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        research_type = request.POST.get('research_type')
        clinic_address = request.POST.get('clinic_address')
        issue_reason = request.POST.get('issue_reason')

        # Create the external direction
        donor = Donor.objects.get(id=donor_id)
        external_direction = ExternalDirection(
            donor=donor,
            issue_date=issue_date,
            start_date=start_date,
            end_date=end_date,
            research_type=research_type,
            clinic_address=clinic_address,
            issue_reason=issue_reason
        )
        external_direction.save()

        # Redirect to a success page or listing
        return redirect('direction_search')
    except Exception as e:
        # Handle errors
        today = datetime.date.today()
        available_dates = [today + datetime.timedelta(days=i) for i in range(30)]
        expiry_dates = [today + datetime.timedelta(days=i) for i in range(180)]

        return render(request, 'external_direction_form.html', {
            'error_message': str(e),
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': available_dates,
            'expiry_dates': expiry_dates,
        })


def external_direction_view(request, direction_id):
    """View an external direction in read-only mode"""
    direction = get_object_or_404(ExternalDirection, id=direction_id)
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    # Generate dates to populate dropdowns in read-only mode
    today = datetime.date.today()
    available_dates = [direction.issue_date, direction.start_date]
    expiry_dates = [direction.end_date]


    # Проверка, может ли пользователь редактировать направление
    try:
        current_user_role = request.session['role']
    except KeyError:
        return render(request, 'direction_menu.html', {"is_first_button": False})

    if current_user_role == 'specialist_med_cart' or current_user_role == 'registrator':
        can_edit = True
    else:
        can_edit = False

    context = {
        'direction': direction,
        'donors': donors,
        'available_dates': available_dates,
        'expiry_dates': expiry_dates,
        'read_only': True,
        'can_edit': can_edit
    }

    return render(request, 'external_direction_form.html', context)


from django.shortcuts import render, get_object_or_404
from .models import Donor, Donation, DirectionBase

from django.shortcuts import render, get_object_or_404
from django.db.models import Count
from .models import Donor, Donation, DirectionBase
import random


def donor_medical_card(request, donor_id):
    """View to display the donor's medical card"""
    donor = get_object_or_404(Donor, id=donor_id)

    # Get donation statistics
    try:
        total_donations = Donation.objects.filter(donor=donor).count()
    except:
        # Fallback if Donation model is not accessible
        total_donations = 0

    # Get external directions (for the "Выдано направление" links)
    external_directions = DirectionBase.objects.filter(
        donor=donor,
        type='external',
        is_completed=False,
        expiry_date__gte=timezone.now().date()
    ).order_by('-created_at')[:3]

    # Get internal directions for the directions list (all types except external)
    internal_directions = DirectionBase.objects.filter(
        donor=donor,
        is_completed=False,
        expiry_date__gte=timezone.now().date()
    ).exclude(type='external').order_by('expiry_date')[:2]

    # Calculate progress circle values
    # These would ideally come from actual data, but for now we'll generate random values
    # that match the design

    # First progress circle (out of 60)
    first_remaining = random.randint(30, 55)  # Random number for demo
    first_total = 60
    first_progress = (first_total - first_remaining) / first_total
    first_progress_offset = 440 - (440 * first_progress)  # 440 is the circumference of the circle

    # Second progress circle (out of 40)
    second_remaining = random.randint(20, 35)  # Random number for demo
    second_total = 40
    second_progress = (second_total - second_remaining) / second_total
    second_progress_offset = 440 - (440 * second_progress)

    personal_data = f"{donor.last_name} {donor.first_name} {donor.middle_name}, Москва,\n{donor.phone}, {donor.email}"

    if donor.kell_factor == '+':
        kell_str = "Kell-фактор: положительный"
    else:
        kell_str = "Kell-фактор: отрицательный"
    donor_data = f"{donor.blood_group}, {kell_str}"

    if donor.is_regular:
        is_regular_text = "Штатный донор"
        is_regular_class = "donor-status-badge"
    else:
        is_regular_text = "Не штатный донор"
        is_regular_class = "donor-status-badge-not-regular"

    # Get direction type descriptions for external directions
    external_directions_with_types = []
    for direction in external_directions:
        # Get the related object (ExternalDirection)
        external_direction = direction.content_object
        if external_direction:
            # Get research type display name
            try:
                research_type_display = dict(external_direction.RESEARCH_TYPE_CHOICES).get(
                    external_direction.research_type, "Другое исследование"
                )
                external_directions_with_types.append({
                    'get_view_url': direction.get_view_url(),
                    'type_display': f"Направление на {research_type_display}"
                })
            except (AttributeError, KeyError):
                # Fallback if something goes wrong
                external_directions_with_types.append({
                    'get_view_url': direction.get_view_url(),
                    'type_display': "Внешнее направление"
                })

    # Get direction type descriptions for internal directions
    internal_directions_with_types = []
    for direction in internal_directions:
        direction_type = direction.type
        type_display = ""

        if direction_type == 'examination':
            type_display = "Направление на осмотр"
        elif direction_type == 'analysis':
            type_display = "Направление на анализ периферической крови"
        elif direction_type == 'donation':
            type_display = "Направление на донацию"
        else:
            type_display = "Направление"

        internal_directions_with_types.append({
            'get_view_url': direction.get_view_url(),
            'type_display': type_display
        })

    context = {
        'donor': donor,
        'total_donations': total_donations,
        'external_directions': external_directions_with_types,
        'internal_directions': internal_directions_with_types,
        'first_progress_offset': first_progress_offset,
        'second_progress_offset': second_progress_offset,
        'first_remaining': first_remaining,  # Добавляем количество оставшихся
        'second_remaining': second_remaining,  # Добавляем количество оставшихся
        'first_total': first_total,  # Общее количество для первого круга
        'second_total': second_total,  # Общее количество для второго круга
        'personal_data': personal_data,
        'donor_data': donor_data,
        'is_regular_class': is_regular_class,
        'is_regular_text': is_regular_text,
    }

    return render(request, 'donor_medical_card.html', context)


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Max
from .models import Donor, Donation, BloodComponent
import datetime


def get_next_donation_id():
    """Get the next donation ID"""
    max_id = Donation.objects.aggregate(Max('id'))['id__max'] or 0
    return max_id + 1


def donation_form(request, donor_id=None):
    """View to display the donation creation form"""
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    if donor_id:
        donor = donors.get(id=donor_id)
    else:
        donor = None
    # Generate dates for the next 30 days
    today = datetime.date.today()
    available_dates = [today - datetime.timedelta(days=i) for i in range(30)]  # Past dates for donation

    context = {
        'donors': donors,
        'donor_pre_inf': donor,
        'available_dates': available_dates,
        'next_donation_id': get_next_donation_id(),
        'is_edit': False
    }
    return render(request, 'donation_form.html', context)


@require_http_methods(["POST"])
def donation_create(request):
    """View to handle the form submission"""
    try:
        donor_id = request.POST.get('donor')
        donation_date = request.POST.get('donation_date')
        donation_type = request.POST.get('donation_type')
        payment_requested = request.POST.get('payment_requested')
        certificate_number = request.POST.get('certificate_number', '')

        # Determine payment type based on the checkbox
        payment_type = 'paid' if payment_requested == 'yes' else 'free'

        # Create the donation
        donor = Donor.objects.get(id=donor_id)
        donation = Donation(
            donor=donor,
            donation_date=donation_date,
            donation_type=donation_type,
            payment_type=payment_type,
            donation_location='station',  # Default value
            contraindications='absent',  # Default value
            directions_needed='not_required',  # Default value
            certificate_number=certificate_number
        )
        donation.save()

        # Update donor's donation count
        donor.donation_count += 1
        donor.save()

        # Redirect to a success page or listing
        return redirect(f'/app/donation/view/{donation.id}')
    except Exception as e:
        # Handle errors
        today = datetime.date.today()
        available_dates = [today - datetime.timedelta(days=i) for i in range(30)]

        return render(request, 'donation_form.html', {
            'error_message': str(e),
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': available_dates,
            'next_donation_id': get_next_donation_id()
        })


def donation_view(request, donation_id):
    """View a donation in read-only mode"""
    donation = get_object_or_404(Donation, id=donation_id)
    donors = Donor.objects.all().order_by('last_name', 'first_name')
    donor = Donor.objects.get(id=donation.donor.id)

    # Generate dates to populate dropdowns in read-only mode
    available_dates = [donation.donation_date]

    try:
        current_user_role = request.session['role']
        is_edit = (current_user_role == "registrator")
    except KeyError:
        is_edit = False

    context = {
        'donation': donation,
        'donors': donors,
        'donor_pre_inf': donor,
        'available_dates': available_dates,
        'read_only': True,
        'is_edit': is_edit,  # You can control this based on permissions,
        'is_edit_allowed': is_edit
    }

    return render(request, 'donation_form.html', context)


def donation_edit(request, donation_id):
    """View to edit an existing donation"""
    donation = get_object_or_404(Donation, id=donation_id)
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    # Generate dates
    today = datetime.date.today()
    available_dates = [today - datetime.timedelta(days=i) for i in range(30)]

    # Ensure the donation date is included in available dates
    if donation.donation_date not in available_dates:
        available_dates.append(donation.donation_date)
        available_dates.sort(reverse=True)

    context = {
        'donation': donation,
        'donors': donors,
        'available_dates': available_dates,
        'is_edit': True
    }

    return render(request, 'donation_form.html', context)


@require_http_methods(["POST"])
def donation_update(request, donation_id):
    """View to handle the update form submission"""
    try:
        donation = get_object_or_404(Donation, id=donation_id)

        donor_id = request.POST.get('donor')
        donation_date = request.POST.get('donation_date')
        donation_type = request.POST.get('donation_type')
        payment_requested = request.POST.get('payment_requested')
        certificate_number = request.POST.get('certificate_number', '')

        # Determine payment type based on the checkbox
        payment_type = 'paid' if payment_requested == 'yes' else 'free'

        # Update the donation
        donor = Donor.objects.get(id=donor_id)
        donation.donor = donor
        donation.donation_date = donation_date
        donation.donation_type = donation_type
        donation.payment_type = payment_type
        donation.certificate_number = certificate_number
        donation.save()

        # Redirect to the donation view
        return redirect('donation_search')
    except Exception as e:
        # Handle errors
        today = datetime.date.today()
        available_dates = [today - datetime.timedelta(days=i) for i in range(30)]

        return render(request, 'donation_form.html', {
            'error_message': str(e),
            'donation': donation,
            'donors': Donor.objects.all().order_by('last_name', 'first_name'),
            'available_dates': available_dates,
            'is_edit': True
        })


from django.shortcuts import render
from django.utils import timezone
import datetime
from .models import Donor, Donation


def donation_search(request):
    """View for searching and listing donations"""
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    # Get filter parameters
    donor_id = request.GET.get('donor', '')
    date_filter = request.GET.get('date', '')
    donation_type = request.GET.get('donation_type', '')
    blood_group = request.GET.get('blood_group', '')
    rh_factor = request.GET.get('rh_factor', '')
    donor_returned = request.GET.get('donor_returned', 'any')

    # Start with all donations
    donations = Donation.objects.all().order_by('-donation_date')

    # Apply filters
    if donor_id:
        donations = donations.filter(donor_id=donor_id)

    if date_filter:
        today = timezone.now().date()
        if date_filter == 'today':
            donations = donations.filter(donation_date=today)
        elif date_filter == 'week':
            week_ago = today - datetime.timedelta(days=7)
            donations = donations.filter(donation_date__gte=week_ago)
        elif date_filter == 'month':
            month_ago = today - datetime.timedelta(days=30)
            donations = donations.filter(donation_date__gte=month_ago)
        elif date_filter == 'year':
            year_ago = today - datetime.timedelta(days=365)
            donations = donations.filter(donation_date__gte=year_ago)

    if donation_type:
        donations = donations.filter(donation_type=donation_type)

    if blood_group:
        donations = donations.filter(donor__blood_group=blood_group)

    if rh_factor:
        donations = donations.filter(donor__rh_factor=rh_factor)

    if donor_returned != 'any':
        # This is a more complex query - requires additional logic
        # For "returned" donors, we would find donors with multiple donations
        if donor_returned == 'yes':
            # Find donors with more than one donation
            donor_ids_with_multiple_donations = Donation.objects.values('donor') \
                .annotate(count=Count('id')) \
                .filter(count__gt=1) \
                .values_list('donor', flat=True)
            donations = donations.filter(donor__id__in=donor_ids_with_multiple_donations)
        else:  # 'no'
            # Find donors with only one donation
            donor_ids_with_single_donation = Donation.objects.values('donor') \
                .annotate(count=Count('id')) \
                .filter(count=1) \
                .values_list('donor', flat=True)
            donations = donations.filter(donor__id__in=donor_ids_with_single_donation)

    context = {
        'donors': donors,
        'donations': donations,
        'selected_donor': donor_id,
        'selected_date': date_filter,
        'selected_type': donation_type,
        'selected_blood_group': blood_group,
        'selected_rh_factor': rh_factor,
        'selected_returned': donor_returned
    }

    return render(request, 'donation_search.html', context)


def get_file(request, document_id):
    document = PaymentApplication.objects.get(id=document_id)
    return FileResponse(document.file.open(), as_attachment=True, filename=document.file.name)


def analytics_view(request):
    return render(request, 'analytics.html')


from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Donor



def donor_view(request, donor_id):
    """View a donor's information in read-only mode"""
    donor = get_object_or_404(Donor, id=donor_id)
    try:
        current_user_role = request.session['role']
        is_can_edit = (current_user_role == "registrator")
    except KeyError:
        is_can_edit = False
    context = {
        'donor': donor,
        'read_only': True,
        'can_edit': is_can_edit,  # Allow editing option
    }

    return render(request, 'donor_personal_data.html', context)


def donor_create(request):
    """View to create a new donor"""
    if request.method == 'POST':
        try:
            # Extract data from the form
            last_name = request.POST.get('last_name')
            first_name = request.POST.get('first_name')
            middle_name = request.POST.get('middle_name')
            snils = request.POST.get('snils')
            document_number = request.POST.get('document_number')
            blood_group = request.POST.get('blood_group')
            rh_factor = request.POST.get('rh_factor')
            kell_factor = request.POST.get('kell_factor')
            registration_address = request.POST.get('registration_address')
            fact_address = request.POST.get('fact_address')
            phone = request.POST.get('phone')
            email = request.POST.get('email')

            # Optional fields with defaults
            last_weight = request.POST.get('last_weight') or 0
            height = request.POST.get('height') or None
            last_pressure = request.POST.get('last_pressure') or "120/80"
            is_regular = 'is_regular' in request.POST

            # Handle the same address checkbox
            if 'same_address' in request.POST:
                fact_address = registration_address

            # Create a new donor
            donor = Donor(
                last_name=last_name,
                first_name=first_name,
                middle_name=middle_name,
                snils=snils,
                document_number=document_number,
                blood_group=blood_group,
                rh_factor=rh_factor,
                kell_factor=kell_factor,
                registration_address=registration_address,
                fact_address=fact_address,
                last_weight=last_weight,
                height=height,
                last_pressure=last_pressure,
                is_regular=is_regular,
                phone=phone,
                email=email
            )
            donor.save()

            messages.success(request, 'Донор успешно создан')
            return redirect('donor_view', donor_id=donor.id)

        except Exception as e:
            messages.error(request, f'Ошибка при создании донора: {str(e)}')
            return render(request, 'donor_form.html', {'error': str(e)})

    # GET request - show the form
    return render(request, 'donor_personal_data.html')


def donor_edit(request, donor_id):
    """View to edit an existing donor"""
    donor = get_object_or_404(Donor, id=donor_id)

    if request.method == 'POST':
        try:
            # Extract data from the form
            donor.last_name = request.POST.get('last_name')
            donor.first_name = request.POST.get('first_name')
            donor.middle_name = request.POST.get('middle_name')
            donor.snils = request.POST.get('snils')
            donor.document_number = request.POST.get('document_number')
            donor.registration_address = request.POST.get('registration_address')
            donor.fact_address = request.POST.get('fact_address')
            donor.phone = request.POST.get('phone')
            donor.email = request.POST.get('email')

            # Optional fields
            if request.POST.get('last_weight'):
                donor.last_weight = request.POST.get('last_weight')
            if request.POST.get('height'):
                donor.height = request.POST.get('height')
            if request.POST.get('last_pressure'):
                donor.last_pressure = request.POST.get('last_pressure')

            donor.is_regular = 'is_regular' in request.POST

            # Handle the same address checkbox
            if 'same_address' in request.POST:
                donor.fact_address = donor.registration_address

            donor.save()

            messages.success(request, 'Данные донора успешно обновлены')
            return redirect('donor_view', donor_id=donor.id)

        except Exception as e:
            print(e)
            messages.error(request, f'Ошибка при обновлении данных донора: {str(e)}')
            return render(request, 'donor_personal_data.html', {'donor': donor, 'error': str(e)})

    # GET request - show the form with donor data
    return render(request, 'donor_personal_data.html', {'donor': donor})


from django.contrib import messages
from django.http import JsonResponse
from .models import Donor, DonorCard
import json
import datetime


def donor_card_view(request, card_id):
    """View a donor card in read-only mode"""
    donor_card = get_object_or_404(DonorCard, id=card_id)
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    # Список доступных противопоказаний
    contraindication_list = [
        "сыпной_тиф",
        "туляремия",
        "лепра",
        "африканский_трипаносомоз",
        "болезнь_Чагаса",
        "лейшманиоз",
        "токсоплазмоз"
    ]

    context = {
        'donor_card': donor_card,
        'donors': donors,
        'read_only': True,
        'can_edit': True,  # Allow editing option
        'contraindications': contraindication_list,
    }

    return render(request, 'donor_card_form.html', context)


def donor_card_create(request):
    """View to create a new donor card"""
    if request.method == 'POST':
        try:
            # Extract data from the form
            donor_id = request.POST.get('donor')
            birth_date = request.POST.get('birth_date')
            # Получаем противопоказания из формы
            contraindications_str = request.POST.get('contraindications', '')
            contraindications = contraindications_str.split(',') if contraindications_str else []

            height = request.POST.get('height')
            weight = request.POST.get('weight')
            blood_group = request.POST.get('blood_group')
            rh_factor = request.POST.get('rh_factor')
            kell_factor = request.POST.get('kell_factor')

            # Process available donation types
            donation_types_str = request.POST.get('available_donation_types', '')
            available_donation_types = donation_types_str.split(',') if donation_types_str else []

            # Create a new donor card
            donor = Donor.objects.get(id=donor_id)
            donor_card = DonorCard(
                donor=donor,
                birth_date=birth_date,
                contraindications=contraindications,  # Используем новое поле
                height=height,
                weight=weight,
                blood_group=blood_group,
                rh_factor=rh_factor,
                kell_factor=kell_factor,
                available_donation_types=available_donation_types
            )
            donor_card.save()

            # Update donor's information with the same values
            donor.blood_group = blood_group
            donor.rh_factor = rh_factor
            donor.kell_factor = kell_factor
            donor.height = height
            donor.last_weight = weight
            donor.save()

            messages.success(request, 'Карточка донора успешно создана')
            return redirect('donor_card_view', card_id=donor_card.id)

        except Exception as e:
            messages.error(request, f'Ошибка при создании карточки донора: {str(e)}')
            return render(request, 'donor_card_form.html', {
                'donors': Donor.objects.all().order_by('last_name', 'first_name'),
                'error': str(e)
            })

    # GET request - show the form
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    # Список доступных противопоказаний
    contraindication_list = [
        "сыпной_тиф",
        "туляремия",
        "лепра",
        "африканский_трипаносомоз",
        "болезнь_Чагаса",
        "лейшманиоз",
        "токсоплазмоз"
    ]

    return render(request, 'donor_card_form.html', {
        'donors': donors,
        'contraindications': contraindication_list
    })


def donor_card_edit(request, card_id):
    """View to edit an existing donor card"""
    donor_card = get_object_or_404(DonorCard, id=card_id)

    if request.method == 'POST':
        try:
            # Extract data from the form
            donor_id = request.POST.get('donor')
            donor_card.birth_date = request.POST.get('birth_date')

            # Получаем противопоказания из формы
            contraindications_str = request.POST.get('contraindications', '')
            donor_card.contraindications = contraindications_str.split(',') if contraindications_str else []

            donor_card.height = request.POST.get('height')
            donor_card.weight = request.POST.get('weight')
            donor_card.blood_group = request.POST.get('blood_group')
            donor_card.rh_factor = request.POST.get('rh_factor')
            donor_card.kell_factor = request.POST.get('kell_factor')

            # Process available donation types
            donation_types_str = request.POST.get('available_donation_types', '')
            donor_card.available_donation_types = donation_types_str.split(',') if donation_types_str else []

            # Update donor relation if changed
            if donor_id != str(donor_card.donor.id):
                donor_card.donor = Donor.objects.get(id=donor_id)

            donor_card.save()

            # Update donor's information with the same values
            donor = donor_card.donor
            donor.blood_group = donor_card.blood_group
            donor.rh_factor = donor_card.rh_factor
            donor.kell_factor = donor_card.kell_factor
            donor.height = donor_card.height
            donor.last_weight = donor_card.weight
            donor.save()

            messages.success(request, 'Карточка донора успешно обновлена')
            return redirect('donor_card_view', card_id=donor_card.id)

        except Exception as e:
            messages.error(request, f'Ошибка при обновлении карточки донора: {str(e)}')
            return render(request, 'donor_card_form.html', {
                'donor_card': donor_card,
                'donors': Donor.objects.all().order_by('last_name', 'first_name'),
                'error': str(e)
            })

    # GET request - show the form with donor card data
    donors = Donor.objects.all().order_by('last_name', 'first_name')

    # Список доступных противопоказаний
    contraindication_list = [
        "сыпной_тиф",
        "туляремия",
        "лепра",
        "африканский_трипаносомоз",
        "болезнь_Чагаса",
        "лейшманиоз",
        "токсоплазмоз"
    ]

    return render(request, 'donor_card_form.html', {
        'donor_card': donor_card,
        'donors': donors,
        'contraindications': contraindication_list
    })