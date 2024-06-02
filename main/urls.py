from main import views

from django.urls import path


urlpatterns = [
    path("", views.index, name="index"),
    path("add-contact/", views.ContactCreate.as_view(), name="contact_create"),
    path("contacts/", views.ContactList.as_view(), name="contact_list"),
    path("add-domain/", views.DomainCreate.as_view(), name="domain_create"),
]
