# models.py
import random

from django.db import models
from django.utils import timezone
import datetime
from django.contrib.contenttypes.fields import GenericRelation
from django.dispatch import receiver
from django.db.models.signals import post_save

class BloodComponent(models.Model):
    name = models.CharField(max_length=50, verbose_name="Название компонента")

    def __str__(self):
        return self.name


class Donor(models.Model):
    BLOOD_GROUP_CHOICES = [
        ('O', 'O'),
        ('A', 'A'),
        ('B', 'B'),
        ('AB', 'AB'),
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
    document_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер документа")
    registration_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Адрес регистрации")
    fact_address = models.CharField(max_length=255, blank=True, null=True, verbose_name="Фактический адрес")
    # Add this field to your Donor model
    height = models.IntegerField(verbose_name="Рост (см)", null=True, blank=True)
    # Добавляем поле для связи с компонентами крови, если его еще нет
    blood_components = models.ManyToManyField('BloodComponent', blank=True, verbose_name="Компоненты крови")
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Телефонный номер")
    email = models.EmailField(blank=True, null=True, verbose_name="Адрес электронной почты")
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
    # Add certificate_number field to the Donation model
    certificate_number = models.CharField(max_length=50, blank=True, null=True, verbose_name="Номер справки о донации")

    def __str__(self):
        return f"Донация {self.donor} от {self.donation_date}"

    class Meta:
        verbose_name = "Донация"
        verbose_name_plural = "Донации"
        ordering = ['-donation_date']


from django.db import models
from django.utils import timezone


class DonorCard(models.Model):
    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, related_name='donor_cards', verbose_name="Донор")
    birth_date = models.DateField(verbose_name="Дата рождения")
    # Заменяем has_contraindications на contraindications
    contraindications = models.JSONField(default=list, verbose_name="Выявленные противопоказания")
    height = models.IntegerField(verbose_name="Рост (см)")
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Вес (кг)")
    blood_group = models.CharField(max_length=3, verbose_name="Группа крови")
    rh_factor = models.CharField(max_length=1, verbose_name="Rh-фактор")
    kell_factor = models.CharField(max_length=1, verbose_name="Kell-фактор")

    # Available donation types (stored as JSON array)
    available_donation_types = models.JSONField(default=list, verbose_name="Доступные типы донации")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Карточка донора {self.donor.get_full_name()}"

    class Meta:
        verbose_name = "Карточка донора"
        verbose_name_plural = "Карточки доноров"
        ordering = ['-created_at']


class Payment(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('accumulative', 'По накопительной системе'),
        ('standard', 'Стандартная выплата')
    ]

    PAYMENT_TYPE_CHOICES = [
        ('social_support', 'Социальная поддержка'),
        ('payment', 'Оплата'),
        ('compensation', 'Компенсация'),
    ]

    donation = models.ForeignKey('Donation', on_delete=models.CASCADE, related_name='payments', verbose_name="Донация")
    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, related_name='payments', verbose_name="Донор")
    payment_date = models.DateField(verbose_name="Дата выплаты")
    expiration_date = models.DateField(verbose_name="Срок истечения")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, verbose_name="Метод выплаты")
    is_paid_donation = models.BooleanField(default=False, verbose_name="Донация на платной основе")
    food_compensation = models.BooleanField(default=False, verbose_name="Компенсация за питание")
    amount = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Сумма выплаты (в рублях)")
    document_id = models.CharField(max_length=50, blank=True, null=True,
                                   verbose_name="Номер документа, удостоверяющего личность")
    document_type = models.CharField(max_length=50, blank=True, null=True, verbose_name="Тип документа")
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, verbose_name="Вид выплаты")
    is_payment_processed = models.BooleanField(default=False, verbose_name="Выплата произведена")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def save(self, *args, **kwargs):
        # Автоматически устанавливаем срок истечения на следующий день после даты донации
        if self.donation and not self.expiration_date:
            self.expiration_date = self.donation.donation_date + datetime.timedelta(days=1)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Выплата {self.donor} от {self.payment_date} на сумму {self.amount} руб."

    class Meta:
        verbose_name = "Выплата"
        verbose_name_plural = "Выплаты"
        ordering = ['-payment_date']


# models.py
from django.db import models


class PaymentApplication(models.Model):
    payment = models.ForeignKey('Payment', on_delete=models.CASCADE, related_name='applications')
    file = models.FileField(upload_to='payment_applications/')
    upload_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Заявление на выплату #{self.id} для платежа #{self.payment.id}"


from django.db import models
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
import datetime


class DirectionBase(models.Model):
    """
    A model that links to all direction types and provides common functionality
    for searching and displaying directions.
    """
    DIRECTION_TYPE_CHOICES = [
        ('examination', 'На осмотр'),
        ('analysis', 'На исследование'),
        ('donation', 'На донацию'),
        ('external', 'Внешнее'),
    ]

    DIRECTION_LOCATION_CHOICES = [
        ('internal', 'Внутреннее'),
        ('external', 'Внешнее (в поликлинику)'),
    ]

    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, related_name='directions', verbose_name="Донор")
    type = models.CharField(max_length=20, choices=DIRECTION_TYPE_CHOICES, verbose_name="Тип направления")
    location = models.CharField(max_length=20, choices=DIRECTION_LOCATION_CHOICES, verbose_name="Вид направления",
                                default='internal')

    # Generic relation to the actual direction
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey('content_type', 'object_id')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    expiry_date = models.DateField(verbose_name="Срок действия до", blank=True, null=True)
    is_completed = models.BooleanField(default=False, verbose_name="Выполнено")

    def __str__(self):
        return f"{self.get_type_display()} для {self.donor} от {self.created_at.strftime('%d.%m.%Y')}"

    @property
    def is_expired(self):
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    @property
    def status(self):
        if self.is_completed:
            return "completed"
        if self.is_expired:
            return "expired"
        return "active"

    def get_view_url(self):
        """
        Get URL for viewing this direction in read-only mode
        """
        if self.type == 'examination':
            return f"/app/examination-direction/view/{self.object_id}/"
        elif self.type == 'analysis':
            return f"/app/blood-analysis-direction/view/{self.object_id}/"
        elif self.type == 'donation':
            return f"/app/donation-direction/view/{self.object_id}/"
        elif self.type == 'external':
            return f"/app/external-direction/view/{self.object_id}/"
        return "#"

    class Meta:
        verbose_name = "Направление"
        verbose_name_plural = "Направления"
        ordering = ['-created_at']


class DonationDirection(models.Model):
    DONATION_TYPE_CHOICES = [
        ('whole_blood', 'Цельная кровь'),
        ('plasma', 'Плазма'),
        ('platelets', 'Тромбоциты'),
        ('erythrocytes', 'Эритроциты'),
        ('granulocytes', 'Гранулоциты'),
    ]

    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, related_name='donation_directions',
                              verbose_name="Донор")
    direction_date = models.DateField(default=timezone.now, verbose_name="Дата донации")
    blood_group = models.CharField(max_length=3, verbose_name="Группа крови", blank=True)
    rh_factor = models.CharField(max_length=1, verbose_name="Rh-фактор", blank=True)
    document_number = models.CharField(max_length=50, verbose_name="Номер документа, удостоверяющего личность",
                                       blank=True)
    donation_number = models.CharField(max_length=50, verbose_name="Номер донации", blank=True)
    previous_donation_number = models.CharField(max_length=50, verbose_name="Номер предыдущей донации", blank=True,
                                                null=True)
    previous_donation_date = models.DateField(verbose_name="Дата предыдущей донации", blank=True, null=True)
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, verbose_name="Тип донации",
                                     blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    base_direction = GenericRelation('DirectionBase')

    def __str__(self):
        return f"Направление {self.donor} от {self.direction_date}"

    class Meta:
        verbose_name = "Направление на донацию"
        verbose_name_plural = "Направления на донацию"
        ordering = ['-direction_date']


@receiver(post_save, sender=DonationDirection)
def create_base_direction(sender, instance, created, **kwargs):
    if created:
        from .models import DirectionBase  # Import here to avoid circular import
        content_type = ContentType.objects.get_for_model(instance)

        # Calculate expiry date (30 days from creation by default)
        if type(instance.direction_date) is str:
            # Convert string to date object
            instance.direction_date = datetime.datetime.strptime(instance.direction_date, "%Y-%m-%d").date()
        else:
            f = instance.direction_date
        expiry_date = f + datetime.timedelta(days=30)

        DirectionBase.objects.create(
            donor=instance.donor,
            type='donation',
            location='internal',
            content_type=content_type,
            object_id=instance.id,
            expiry_date=expiry_date
        )


from django.db import models
from django.utils import timezone


class ExaminationDirection(models.Model):
    DONATION_TYPE_CHOICES = [
        ('whole_blood', 'Цельная кровь'),
        ('plasma', 'Плазма'),
        ('platelets', 'Тромбоциты'),
        ('erythrocytes', 'Эритроциты'),
        ('granulocytes', 'Гранулоциты'),
    ]

    YES_NO_CHOICES = [
        ('yes', 'Да'),
        ('no', 'Нет'),
    ]

    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, related_name='examination_directions',
                              verbose_name="Донор")
    planned_donation_date = models.DateField(verbose_name="Дата предполагаемой донации")
    document_number = models.CharField(max_length=50, verbose_name="Номер документа, удостоверяющего личность",
                                       blank=True)
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, verbose_name="Тип донации",
                                     blank=True)
    blood_group = models.CharField(max_length=3, verbose_name="Группа крови", blank=True)
    rh_factor = models.CharField(max_length=1, verbose_name="Rh-фактор", blank=True)

    # Medical examination fields
    has_complaints = models.CharField(max_length=3, choices=YES_NO_CHOICES, verbose_name="Есть ли жалобы?")
    has_contraindications = models.CharField(max_length=3, choices=YES_NO_CHOICES,
                                             verbose_name="Имеются ли в анамнезе заболевания из перечня противопоказаний?")
    normal_mucous = models.CharField(max_length=3, choices=YES_NO_CHOICES,
                                     verbose_name="Склеры, видимые слизистые (полости рта, носа) нормально окрашены?")
    clean_skin = models.CharField(max_length=3, choices=YES_NO_CHOICES,
                                  verbose_name="Кожа чистая, лимфоузлы не увеличены?")
    normal_cardiac = models.CharField(max_length=3, choices=YES_NO_CHOICES,
                                      verbose_name="Выявлены ли патологии при аускультации сердца и легких?")
    normal_abdomen = models.CharField(max_length=3, choices=YES_NO_CHOICES,
                                      verbose_name="Есть ли отклонения в органах брюшной полости?")
    recent_operations = models.CharField(max_length=3, choices=YES_NO_CHOICES,
                                         verbose_name="Были ли операции/вакцинации в течение последних 2 месяцев?")

    # Vital signs
    blood_pressure = models.CharField(max_length=7, verbose_name="Значение артериального давления", blank=True)
    pulse = models.IntegerField(verbose_name="Пульс", null=True, blank=True)
    temperature = models.DecimalField(max_digits=3, decimal_places=1, verbose_name="Температура тела", null=True,
                                      blank=True)
    height = models.IntegerField(verbose_name="Рост (см)", null=True, blank=True)
    weight = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Вес (кг)", null=True, blank=True)

    is_approved = models.BooleanField(default=False, verbose_name="Допущен к донации")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    base_direction = GenericRelation('DirectionBase')

    def __str__(self):
        return f"Осмотр {self.donor} от {self.created_at.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Направление на осмотр"
        verbose_name_plural = "Направления на осмотр"
        ordering = ['-created_at']


@receiver(post_save, sender=ExaminationDirection)
def create_base_direction(sender, instance, created, **kwargs):
    if created:
        from .models import DirectionBase  # Import here to avoid circular import
        content_type = ContentType.objects.get_for_model(instance)

        # Calculate expiry date (7 days from planned donation date by default)
        expiry_date = instance.created_at + datetime.timedelta(random.randint(3, 14))

        DirectionBase.objects.create(
            donor=instance.donor,
            type='examination',
            location='internal',
            content_type=content_type,
            object_id=instance.id,
            expiry_date=expiry_date,
            is_completed=instance.is_approved  # If approved, mark as completed
        )


from django.db import models
from django.utils import timezone


class BloodAnalysisDirection(models.Model):
    DONATION_TYPE_CHOICES = [
        ('whole_blood', 'Цельная кровь'),
        ('plasma', 'Плазма'),
        ('platelets', 'Тромбоциты'),
        ('erythrocytes', 'Эритроциты'),
        ('granulocytes', 'Гранулоциты'),
    ]

    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, related_name='blood_analysis_directions',
                              verbose_name="Донор")
    planned_donation_date = models.DateField(verbose_name="Дата предполагаемой донации")
    document_number = models.CharField(max_length=50, verbose_name="Номер документа, удостоверяющего личность",
                                       blank=True)
    donation_type = models.CharField(max_length=20, choices=DONATION_TYPE_CHOICES, verbose_name="Тип донации",
                                     blank=True)
    blood_group = models.CharField(max_length=3, verbose_name="Группа крови", blank=True)
    rh_factor = models.CharField(max_length=1, verbose_name="Rh-фактор", blank=True)
    kell_factor = models.CharField(max_length=1, verbose_name="Kell-фактор", blank=True)

    # Blood analysis parameters
    hemoglobin = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Показатель гемоглобина", null=True,
                                     blank=True)
    erythrocytes_count = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Количество эритроцитов",
                                             null=True, blank=True)
    platelets_count = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Количество тромбоцитов",
                                          null=True, blank=True)
    leukocytes_count = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Количество лейкоцитов",
                                           null=True, blank=True)
    albumin = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Альбумин", null=True, blank=True)
    globulin = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="Глобулин", null=True, blank=True)

    # Additional parameters
    soe = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="СОЭ", null=True, blank=True)
    hct = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="HCT", null=True, blank=True)
    mcv = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="MCV", null=True, blank=True)
    mch = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="MCH", null=True, blank=True)
    mchc = models.DecimalField(max_digits=5, decimal_places=2, verbose_name="MCHC", null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")
    base_direction = GenericRelation('DirectionBase')

    def __str__(self):
        return f"Анализ крови {self.donor} от {self.created_at.strftime('%d.%m.%Y')}"

    class Meta:
        verbose_name = "Направление на анализ периферической крови"
        verbose_name_plural = "Направления на анализ периферической крови"
        ordering = ['-created_at']


@receiver(post_save, sender=BloodAnalysisDirection)
def create_base_direction(sender, instance, created, **kwargs):
    if created:
        from .models import DirectionBase  # Import here to avoid circular import
        content_type = ContentType.objects.get_for_model(instance)

        # Calculate expiry date (14 days from planned donation date by default)
        expiry_date = instance.created_at + datetime.timedelta(random.randint(3, 14))

        DirectionBase.objects.create(
            donor=instance.donor,
            type='analysis',
            location='internal',
            content_type=content_type,
            object_id=instance.id,
            expiry_date=expiry_date
        )


from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
import datetime


class ExternalDirection(models.Model):
    RESEARCH_TYPE_CHOICES = [
        ('ecg', 'ЭКГ'),
        ('self_sample', 'Анализ самозаборных материалов'),
        ('ent', 'Осмотр у врача-оториноларинголога'),
        ('blood_test', 'Анализ крови'),
        ('urine_test', 'Анализ мочи'),
        ('ultrasound', 'УЗИ'),
        ('other', 'Другое'),
    ]

    donor = models.ForeignKey('Donor', on_delete=models.CASCADE, related_name='external_directions',
                              verbose_name="Донор")
    issue_date = models.DateField(verbose_name="Дата выдачи")
    start_date = models.DateField(verbose_name="Дата начала действия")
    end_date = models.DateField(verbose_name="Дата завершения")
    research_type = models.CharField(max_length=20, choices=RESEARCH_TYPE_CHOICES, verbose_name="Тип исследования")
    clinic_address = models.CharField(max_length=255, verbose_name="Адрес поликлиники", blank=True, null=True)
    issue_reason = models.TextField(verbose_name="Причина выдачи направления", blank=True, null=True)

    # Add a generic relation to DirectionBase
    base_direction = GenericRelation('DirectionBase')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создано")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Обновлено")

    def __str__(self):
        return f"Внешнее направление для {self.donor} от {self.issue_date.strftime('%d.%m.%Y')}"

    def get_research_type_display(self):
        """Returns the display name for the research type"""
        for code, name in self.RESEARCH_TYPE_CHOICES:
            if code == self.research_type:
                return name
        return "Другое"

    class Meta:
        verbose_name = "Внешнее направление"
        verbose_name_plural = "Внешние направления"
        ordering = ['-issue_date']


# Signal to create a DirectionBase when an ExternalDirection is created
@receiver(post_save, sender=ExternalDirection)
def create_base_direction(sender, instance, created, **kwargs):
    if created:
        from .models import DirectionBase  # Import here to avoid circular import
        content_type = ContentType.objects.get_for_model(instance)

        DirectionBase.objects.create(
            donor=instance.donor,
            type='external',  # You might want to add a new type for external directions
            location='external',
            content_type=content_type,
            object_id=instance.id,
            expiry_date=instance.end_date
        )