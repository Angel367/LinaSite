from django.contrib import admin
from .models import Donor, PeripheralBloodTest, BloodComponent
# Register your models here.
admin.site.register(Donor)
admin.site.register(PeripheralBloodTest)
admin.site.register(BloodComponent)
