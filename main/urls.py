from main import views

from django.urls import path


urlpatterns = [
    path("", views.index, name="index"),
    # contacts
    path("add-contact/", views.ContactCreate.as_view(), name="contact_create"),
    path("contacts/", views.ContactList.as_view(), name="contact_list"),
    # domains
    path("add-domain/", views.DomainCreate.as_view(), name="domain_create"),
    # payments
    path("checkout/success/", views.checkout_success, name="checkout_success"),
    path("checkout/failure/", views.checkout_failure, name="checkout_failure"),
]
