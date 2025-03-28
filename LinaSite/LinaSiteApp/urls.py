from .views import *
from django.urls import path, include

urlpatterns = [
    path('main/', index, name='index'),
    path('donor-search/', donor_search, name='donor_search'),
    path('donation/register/', donation_register, name='donation_register'),
    path('api/donor/<int:donor_id>/', get_donor_info, name='get_donor_info'),
]
