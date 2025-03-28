# models.py
from django.db import models
from django.utils import timezone


class BloodComponent(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название компонента")

    def __str__(self):
        return self.name


class Donor(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('O-', 'O-'), ('O+', 'O+'),
        ('A-', 'A-'), ('A+', 'A+'),
        ('B-', 'B-'), ('B+', 'B+'),
        ('AB-', 'AB-'), ('AB+', 'AB+')
    ]

    RH_FACTOR_CHOICES = [('+', 'Положительный'), ('-', 'Отрицательный')]
    KELL_FACTOR_CHOICES = [('+', 'Положительный'), ('-', 'Отрицательный')]

    snils = models.CharField(max_length=14, unique=True, verbose_name="СНИЛС")
    last_name = models.CharField(max_length=50, verbose_name="Фамилия")
    first_name = models.CharField(max_length=50, verbose_name="Имя")
    middle_name = models.CharField(max_length=50, verbose_name="Отчество", blank=True, null=True)
    blood_group = models.CharField(max_length=3, choices=BLOOD_GROUP_CHOICES, verbose_name="Группа крови")
    rh_factor = models.CharField(max_length=1, choices=RH_FACTOR_CHOICES, verbose_name="Rh-фактор")
    kell_factor = models.CharField(max_length=1, choices=KELL_FACTOR_CHOICES, verbose_name="Kell-фактор")
    last_weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Последний вес (кг)")
    last_pressure = models.CharField(max_length=7, verbose_name="Последнее давление")
    is_regular = models.BooleanField(default=False, verbose_name="Штатный донор")
    donation_count = models.PositiveIntegerField(default=0, verbose_name="Количество донаций")

    # Добавляем поле для связи с компонентами крови, если его еще нет
    blood_components = models.ManyToManyField('BloodComponent', blank=True, verbose_name="Компоненты крови")

    def __str__(self):
        return f"{self.last_name} {self.first_name} ({self.blood_group}{self.rh_factor})"

    def get_full_name(self):
        if self.middle_name:
            return f"{self.last_name} {self.first_name} {self.middle_name}"
        return f"{self.last_name} {self.first_name}"


class Donation(models.Model):
    DONATION_TYPE_CHOICES = [
        ('whole_blood', 'Цельная кровь'),
        ('plasma', 'Плазма'),
        ('platelets', 'Тромбоциты'),
        ('erythrocytes', 'Эритроциты'),
        ('granulocytes', 'Гранулоциты'),
    ]

    PAYMENT_TYPE_CHOICES = [
        ('free', 'Безвозмездно'),
        ('paid', 'Платно'),
    ]

    DONATION_LOCATION_CHOICES = [
        ('station', 'Стационарный пункт'),
        ('mobile', 'Выездная акция'),
    ]

    CONTRAINDICATION_CHOICES = [
        ('present', 'Противопоказания присутствуют'),
        ('absent', 'Противопоказания отсутствуют'),
        ('unknown', 'Затрудняюсь ответить'),
    ]

    DIRECTION_CHOICES = [
        ('required', 'Направления необходимы'),
        ('not_required', 'Направления не нужны'),
    ]

    donor = models.ForeignKey(Donor, on_delete=models.CASCADE, related_name='donations', verbose_name="Донор")
    donation_date = models.DateField(default=timezone.now, verbose_name="Дата донации")
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, verbose_name="Тип донации")
    components = models.ManyToManyField(BloodComponent, blank=True, verbose_name="Компоненты крови")
    payment_type = models.CharField(max_length=10, choices=PAYMENT_TYPE_CHOICES, verbose_name="Тип оплаты")
    is_first_donation = models.BooleanField(default=False, verbose_name="Первая донация")
    document_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер документа")
    documents_changed = models.BooleanField(default=False, verbose_name="Документы были изменены")
    donation_location = models.CharField(max_length=20, choices=DONATION_LOCATION_CHOICES, verbose_name="Место сдачи")
    donation_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Адрес донации")
    contraindications = models.CharField(max_length=20, choices=CONTRAINDICATION_CHOICES,
                                         verbose_name="Противопоказания")
    contraindication_details = models.TextField(blank=True, null=True, verbose_name="Детали противопоказаний")
    directions_needed = models.CharField(max_length=20, choices=DIRECTION_CHOICES,
                                         verbose_name="Необходимость направлений")
    directions_details = models.TextField(blank=True, null=True, verbose_name="Детали направлений")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Донация {self.donor} от {self.donation_date}"

    class Meta:
        verbose_name = "Донация"
        verbose_name_plural = "Донации"
        ordering = ['-donation_date']


class PeripheralBloodTest(models.Model):
    DONATION_TYPE_CHOICES = [
        ('whole_blood', 'Цельная кровь'),
        ('plasma', 'Плазма'),
        ('platelets', 'Тромбоциты'),
        ('erythrocytes', 'Эритроциты'),
        ('granulocytes', 'Гранулоциты'),
    ]

    donation_date = models.DateField(verbose_name="Дата предполагаемой донации")
    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, verbose_name="Донор")
    document_number = models.CharField(max_length=20, verbose_name="Номер документа, удостоверяющего личность")
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, verbose_name="Тип донации")

    hemoglobin = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Показатель гемоглобина")
    erythrocytes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество эритроцитов")
    platelets = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество тромбоцитов")
    leukocytes = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Количество лейкоцитов")
    albumin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Альбумин")
    globulin = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="Глобулин")

    soe = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True, verbose_name="СОЕ")
    hct = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="HCT")
    mcv = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="MCV")
    mch = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="MCH")
    mchc = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="MCHC")

    def __str__(self):
        return f"Анализ крови для {self.donor} на {self.donation_date}"
