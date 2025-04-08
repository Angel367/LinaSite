from django.contrib import admin
from .models import Donor, BloodComponent
# Register your models here.
admin.site.register(Donor)
admin.site.register(BloodComponent)
