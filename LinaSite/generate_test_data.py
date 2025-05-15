import os
import sys
import django
import random
from datetime import date, timedelta, datetime
from decimal import Decimal

# Настраиваем Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LinaSite.settings')
django.setup()

from LinaSiteApp.models import (
    BloodComponent, Donor, Donation, Payment, DirectionBase,
    DonationDirection, ExaminationDirection, BloodAnalysisDirection, ExternalDirection,
    DonorCard
)
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


def generate_random_snils():
    # Генерируем первые 9 цифр СНИЛС
    snils_digits = [str(random.randint(0, 9)) for _ in range(9)]

    # Форматируем СНИЛС
    formatted_snils = f"{(''.join(snils_digits[:3]))}-{(''.join(snils_digits[3:6]))}-{(''.join(snils_digits[6:9]))}"

    # Добавляем контрольное число (просто случайные 2 цифры для тестовых данных)
    formatted_snils += f" {random.randint(10, 99)}"

    return formatted_snils


def generate_test_data():
    print("Генерация тестовых данных...")

    # Очистка существующих данных
    DirectionBase.objects.all().delete()
    ExternalDirection.objects.all().delete()
    BloodAnalysisDirection.objects.all().delete()
    ExaminationDirection.objects.all().delete()
    DonationDirection.objects.all().delete()
    Payment.objects.all().delete()
    Donation.objects.all().delete()
    DonorCard.objects.all().delete()  # Добавлена очистка DonorCard
    Donor.objects.all().delete()
    BloodComponent.objects.all().delete()

    # Создание компонентов крови - используем только реальные компоненты крови
    components = [
        "Эритроциты", "Тромбоциты", "Плазма",
        "Цельная кровь",
        "Гранулоциты"
    ]

    blood_components = []
    for component in components:
        blood_component = BloodComponent.objects.create(name=component)
        blood_components.append(blood_component)
        print(f"Создан компонент крови: {component}")

    # Русские имена, фамилии и отчества
    first_names = ["Александр", "Сергей", "Дмитрий", "Андрей", "Алексей", "Максим", "Иван", "Николай", "Михаил",
                   "Владимир",
                   "Анна", "Елена", "Мария", "Екатерина", "Наталья", "Ольга", "Татьяна", "Юлия", "Светлана", "Ирина"]

    last_names = ["Иванов", "Смирнов", "Кузнецов", "Попов", "Васильев", "Петров", "Соколов", "Михайлов", "Новиков",
                  "Федоров",
                  "Иванова", "Смирнова", "Кузнецова", "Попова", "Васильева", "Петрова", "Соколова", "Михайлова",
                  "Новикова", "Федорова"]

    middle_names = ["Александрович", "Сергеевич", "Дмитриевич", "Андреевич", "Алексеевич", "Максимович", "Иванович",
                    "Николаевич",
                    "Александровна", "Сергеевна", "Дмитриевна", "Андреевна", "Алексеевна", "Максимовна", "Ивановна",
                    "Николаевна"]

    # Используем только те значения, которые определены в моделях
    blood_groups = ['O-', 'O+', 'A-', 'A+', 'B-', 'B+', 'AB-', 'AB+']
    rh_factors = ['+', '-']
    kell_factors = ['+', '-']

    # Создание доноров
    donors = []
    for i in range(15):
        gender = random.choice(['male', 'female'])

        if gender == 'male':
            first_name = random.choice([n for n in first_names if
                                        n not in ["Анна", "Елена", "Мария", "Екатерина", "Наталья", "Ольга", "Татьяна",
                                                  "Юлия", "Светлана", "Ирина"]])
            last_name = random.choice([n for n in last_names if not n.endswith('а')])
            middle_name = random.choice([n for n in middle_names if not n.endswith('на')])
        else:
            first_name = random.choice([n for n in first_names if
                                        n in ["Анна", "Елена", "Мария", "Екатерина", "Наталья", "Ольга", "Татьяна",
                                              "Юлия", "Светлана", "Ирина"]])
            last_name = random.choice([n for n in last_names if n.endswith('а')])
            middle_name = random.choice([n for n in middle_names if n.endswith('на')])

        blood_group = random.choice(blood_groups)
        rh_factor = blood_group[-1]  # Берем из группы крови
        height = random.randint(150, 200)
        weight = Decimal(str(random.uniform(55.0, 100.0))).quantize(Decimal('0.1'))
        from transliterate import translit
        donor = Donor.objects.create(
            snils=generate_random_snils(),
            last_name=last_name,
            first_name=first_name,
            middle_name=middle_name,
            blood_group=blood_group,
            rh_factor=rh_factor,
            kell_factor=random.choice(kell_factors),
            last_weight=weight,
            last_pressure=f"{random.randint(100, 140)}/{random.randint(60, 90)}",
            is_regular=random.choice([True, False]),
            donation_count=random.randint(0, 20),
            document_number=f"Паспорт {random.randint(4000, 5000)} {random.randint(100000, 999999)}",
            registration_address=f"г. Москва, ул. {random.choice(['Ленина', 'Пушкина', 'Гагарина', 'Мира', 'Советская'])}, д. {random.randint(1, 100)}, кв. {random.randint(1, 100)}",
            fact_address=f"г. Москва, ул. {random.choice(['Ленина', 'Пушкина', 'Гагарина', 'Мира', 'Советская'])}, д. {random.randint(1, 100)}, кв. {random.randint(1, 100)}",
            height=height,
            phone=f"+7{random.randint(9000000000, 9999999999)}",
            # random letters
            email = translit(f"{first_name}{last_name}", 'ru', reversed=True).lower() + "@example.com"
        )

        # Добавляем компоненты крови донору
        donor_components = random.sample(blood_components, random.randint(1, 4))
        donor.blood_components.set(donor_components)

        # Создаем карточку донора
        # Получаем список названий компонентов крови для доступных типов донаций
        available_donation_types = []
        for component in donor_components:
            if component.name == "Эритроциты":
                available_donation_types.append("erythrocytes")
            elif component.name == "Тромбоциты":
                available_donation_types.append("platelets")
            elif component.name == "Плазма":
                available_donation_types.append("plasma")
            elif component.name == "Цельная кровь":
                available_donation_types.append("whole_blood")
            elif component.name == "Гранулоциты":
                available_donation_types.append("granulocytes")

        # Создаем карточку донора
        birth_date = date.today() - timedelta(days=random.randint(6570, 18250))  # от 18 до 50 лет
        donor_card = DonorCard.objects.create(
            donor=donor,
            birth_date=birth_date,
            contraindications=[],
            height=height,
            weight=weight,
            blood_group=blood_group,
            rh_factor=rh_factor,
            kell_factor=donor.kell_factor,
            available_donation_types=available_donation_types
        )

        donors.append(donor)
        print(f"Создан донор: {donor}")
        print(f"Создана карточка донора: {donor_card}")

    # Создание донаций - используем только значения из DONATION_TYPE_CHOICES
    donations = []
    donation_types = ['whole_blood', 'plasma', 'platelets', 'erythrocytes', 'granulocytes']
    payment_types = ['free', 'paid']
    donation_locations = ['station', 'mobile']
    contraindication_choices = ['present', 'absent', 'unknown']
    direction_choices = ['required', 'not_required']

    for donor in donors:
        # Для каждого донора создаем 1-3 донации
        for _ in range(random.randint(1, 3)):
            donation_date = date.today() - timedelta(days=random.randint(1, 105))

            donation = Donation.objects.create(
                donor=donor,
                donation_date=donation_date,
                donation_type=random.choice(donation_types),
                payment_type=random.choice(payment_types),
                is_first_donation=donor.donation_count == 1,
                documents_changed=random.choice([True, False]),
                donation_location=random.choice(donation_locations),
                donation_address=f"г. {random.choice(['Москва', 'Санкт-Петербург', 'Казань', 'Екатеринбург'])}, ул. {random.choice(['Ленина', 'Пушкина', 'Гагарина', 'Мира', 'Советская'])}, д. {random.randint(1, 100)}",
                contraindications=random.choice(contraindication_choices),
                contraindication_details="Отсутствуют" if random.choice(
                    [True, False]) else "Небольшая аллергия на пыльцу",
                directions_needed=random.choice(direction_choices),
                directions_details="Нет необходимости" if random.choice(
                    [True, False]) else "Требуется дополнительное обследование",
                certificate_number=f"СП-{random.randint(1000, 9999)}/{random.randint(2020, 2023)}"
            )

            # Добавляем компоненты крови донации
            donation_components = random.sample(blood_components, random.randint(1, 3))
            donation.components.set(donation_components)

            donations.append(donation)
            print(f"Создана донация: {donation}")

            # Создаем платежи для донаций - используем только значения из моделей
            if donation.payment_type == 'paid':
                payment_date = donation.donation_date + timedelta(days=random.randint(1, 30))
                expiration_date = payment_date + timedelta(days=90)

                payment = Payment.objects.create(
                    donation=donation,
                    donor=donor,
                    payment_date=payment_date,
                    expiration_date=expiration_date,
                    payment_method=random.choice(['accumulative', 'standard']),
                    is_paid_donation=True,
                    food_compensation=random.choice([True, False]),
                    amount=Decimal(str(random.uniform(1000.0, 5000.0))).quantize(Decimal('0.1')),
                    document_id=donor.document_number,
                    document_type="Паспорт",
                    payment_type=random.choice(['social_support', 'payment', 'compensation']),
                    is_payment_processed=random.choice([True, False])
                )

                print(f"Создан платеж: {payment}")

    # Создание направлений на донацию
    for donor in donors:
        if random.choice([True, False]):
            for _ in range(random.randint(1, 4)):
                planned_donation_date = datetime.strptime("2025-02-01", "%Y-%m-%d") + timedelta(days=random.randint(1, 105))

                donation_direction = DonationDirection.objects.create(
                    donor=donor,
                    direction_date=planned_donation_date,
                    created_at=planned_donation_date,
                    blood_group=donor.blood_group,
                    rh_factor=donor.rh_factor,
                    document_number=donor.document_number,
                    donation_number=f"Д-{random.randint(1000, 9999)}/{random.randint(2020, 2023)}",
                    previous_donation_number=f"Д-{random.randint(1000, 9999)}/{random.randint(2019, 2022)}" if random.choice(
                        [True, False]) else None,
                    previous_donation_date=date.today() - timedelta(days=random.randint(30, 180)) if random.choice(
                        [True, False]) else None,
                    donation_type=random.choice(donation_types)
                )

                print(f"Создано направление на донацию: {donation_direction}")

    # Создание направлений на осмотр - используем только варианты YES_NO_CHOICES из моделей
    for donor in donors:
        if random.choice([True, False]):
            for _ in range(random.randint(1, 4)):
                planned_donation_date = datetime.strptime("2025-02-01", "%Y-%m-%d") + timedelta(days=random.randint(1, 105))

                examination_direction = ExaminationDirection.objects.create(
                    donor=donor,
                    planned_donation_date=planned_donation_date,
                    document_number=donor.document_number,
                    donation_type=random.choice(donation_types),
                    blood_group=donor.blood_group,
                    rh_factor=donor.rh_factor,
                    has_complaints=random.choice(['yes', 'no']),
                    has_contraindications=random.choice(['yes', 'no']),
                    normal_mucous=random.choice(['yes', 'no']),
                    clean_skin=random.choice(['yes', 'no']),
                    normal_cardiac=random.choice(['yes', 'no']),
                    normal_abdomen=random.choice(['yes', 'no']),
                    recent_operations=random.choice(['yes', 'no']),
                    blood_pressure=donor.last_pressure,
                    pulse=random.randint(60, 100),
                    temperature=Decimal(str(random.uniform(36.0, 37.0))).quantize(Decimal('0.1')),
                    height=donor.height,
                    weight=donor.last_weight,
                    is_approved=random.choice([True, False])
                )

                print(f"Создано направление на осмотр: {examination_direction}")

    # Создание направлений на анализ крови
    for donor in donors:
        if random.choice([True, False]):
            for _ in range(random.randint(1, 4)):
                planned_donation_date = datetime.strptime("2025-02-01", "%Y-%m-%d") + timedelta(days=random.randint(1, 105))

                blood_analysis_direction = BloodAnalysisDirection.objects.create(
                    donor=donor,
                    planned_donation_date=planned_donation_date,
                    created_at=planned_donation_date,
                    document_number=donor.document_number,
                    donation_type=random.choice(donation_types),
                    blood_group=donor.blood_group,
                    rh_factor=donor.rh_factor,
                    kell_factor=donor.kell_factor,
                    hemoglobin=Decimal(str(random.uniform(120.0, 170.0))).quantize(Decimal('0.01')),
                    erythrocytes_count=Decimal(str(random.uniform(3.5, 5.5))).quantize(Decimal('0.01')),
                    platelets_count=Decimal(str(random.uniform(150.0, 450.0))).quantize(Decimal('0.01')),
                    leukocytes_count=Decimal(str(random.uniform(4.0, 9.0))).quantize(Decimal('0.01')),
                    albumin=Decimal(str(random.uniform(35.0, 50.0))).quantize(Decimal('0.01')),
                    globulin=Decimal(str(random.uniform(20.0, 35.0))).quantize(Decimal('0.01')),
                    soe=Decimal(str(random.uniform(2.0, 15.0))).quantize(Decimal('0.01')),
                    hct=Decimal(str(random.uniform(35.0, 50.0))).quantize(Decimal('0.01')),
                    mcv=Decimal(str(random.uniform(80.0, 100.0))).quantize(Decimal('0.01')),
                    mch=Decimal(str(random.uniform(25.0, 35.0))).quantize(Decimal('0.01')),
                    mchc=Decimal(str(random.uniform(30.0, 38.0))).quantize(Decimal('0.01'))
                )

                print(f"Создано направление на анализ крови: {blood_analysis_direction}")

    # Создание внешних направлений - используем только RESEARCH_TYPE_CHOICES из моделей
    research_types = ['ecg', 'self_sample', 'ent', 'blood_test', 'urine_test', 'ultrasound', 'other']
    for donor in donors:
        if random.choice([True, False]):
            for _ in range(random.randint(1, 4)):
                issue_date = date.today()
                start_date = issue_date + timedelta(days=random.randint(1, 7))
                end_date = start_date + timedelta(days=random.randint(14, 30))

                external_direction = ExternalDirection.objects.create(
                    donor=donor,
                    issue_date=issue_date,
                    start_date=start_date,
                    end_date=end_date,
                    research_type=random.choice(research_types),
                    clinic_address=f"г. Москва, ул. {random.choice(['Ленина', 'Пушкина', 'Гагарина', 'Мира', 'Советская'])}, д. {random.randint(1, 100)}",
                    issue_reason="Необходимо дополнительное обследование перед донацией" if random.choice(
                        [True, False]) else "Плановое обследование донора"
                )

                print(f"Создано внешнее направление: {external_direction}")

    print("Генерация тестовых данных завершена.")


if __name__ == "__main__":
    generate_test_data()