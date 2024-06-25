import stripe
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin

from main import models, centralnic, forms


# Landing - public
def index(request):
    if request.user.is_authenticated:
        return redirect("domain_list")
    return render(request, "main/index.html")


# User accounts
class UserCreate(CreateView):
    form_class = forms.UserCreationForm
    template_name = "main/user_create.html"
    success_message = "welcome to tofunames.com"

    def get_success_url(self):
        return reverse_lazy("index")

    def form_valid(self, form):
        self.object = form.save()
        user = authenticate(
            username=form.cleaned_data.get("username"),
            password=form.cleaned_data.get("password1"),
        )
        login(self.request, user)
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())


# Core: domains and contacts
class DomainList(LoginRequiredMixin, ListView):
    model = models.Domain

    def get_queryset(self):
        return models.Domain.objects.filter(owner=self.request.user, pending=False)


class ContactCreate(LoginRequiredMixin, CreateView):
    model = models.Contact
    fields = [
        "first_name",
        "last_name",
        "street",
        "city",
        "postal",
        "country",
        "phone",
        "email",
    ]
    template_name = "main/contact_create.html"
    success_url = reverse_lazy("contact_list")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.save()
        if settings.UPSTREAM_ENABLED:
            centralnic.create_contact(self.object)
        return super().form_valid(form)


class ContactList(LoginRequiredMixin, ListView):
    model = models.Contact

    def get_queryset(self):
        return models.Contact.objects.filter(owner=self.request.user)


class DomainCreate(LoginRequiredMixin, CreateView):
    model = models.Domain
    fields = [
        "domain_name",
        "contact",
        "nameserver0",
        "nameserver1",
        "nameserver2",
        "nameserver3",
    ]
    template_name = "main/domain_create.html"
    success_url = reverse_lazy("checkout")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["contact"].queryset = models.Contact.objects.filter(
            owner=self.request.user
        )
        return form

    def form_valid(self, form):
        # save domain instance
        self.object = form.save(commit=False)
        self.object.owner = self.request.user
        self.object.pending = True
        self.object.save()

        # create checkout instance
        models.Checkout.objects.create(domain=self.object)

        # start checkout
        stripe.api_key = settings.STRIPE_API_KEY
        checkout_session = stripe.checkout.Session.create(
            customer_email=self.request.user.email,
            line_items=[
                {
                    "price": settings.STRIPE_PRICE,
                    "quantity": 1,
                },
            ],
            mode="payment",
            success_url=f"{settings.CANONICAL_URL}{reverse_lazy('checkout_success')}",
            cancel_url=f"{settings.CANONICAL_URL}{reverse_lazy('checkout_failure')}",
        )
        response = HttpResponseRedirect(checkout_session.url)
        response.status_code = 303
        return response


class DomainUpdate(LoginRequiredMixin, UpdateView):
    model = models.Domain
    fields = [
        "contact",
        "nameserver0",
        "nameserver1",
        "nameserver2",
        "nameserver3",
    ]
    template_name = "main/domain_edit.html"
    success_url = reverse_lazy("index")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["contact"].queryset = models.Contact.objects.filter(
            owner=self.request.user
        )
        return form


# Payments - Stripe
def checkout_success(request):
    domain = models.Domain.objects.get(pending=True, owner=request.user)
    checkout = models.Checkout.objects.get(domain=domain)

    # register domain
    if settings.UPSTREAM_ENABLED:
        centralnic.register_domain(domain)

    # complete registration on success
    checkout.delete()
    domain.pending = False
    domain.save()

    # respond with message
    messages.success(request, "registration complete")
    return redirect("index")


def checkout_failure(request):
    # cleanup pending domain and checkout instances
    domain = models.Domain.objects.filter(pending=True)
    domain.delete()
    models.Checkout.objects.all().delete()

    # respond with message
    messages.error(request, "payment failed")
    return redirect("domain_create")
