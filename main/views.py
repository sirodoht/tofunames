import stripe
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView
from django.views.generic.edit import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from main import models, centralnic


@login_required
def index(request):
    return render(
        request,
        "main/index.html",
        {
            "domain_list": models.Domain.objects.filter(pending=False),
        },
    )


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
        self.object = form.save()
        centralnic.create_contact(self.object)
        return super().form_valid(form)


class ContactList(LoginRequiredMixin, ListView):
    model = models.Contact


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

    def form_valid(self, form):
        # save domain instance
        self.object = form.save(commit=False)
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
                    "price": "price_1PO27uKcGejlgwEvMViklyCs",
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


def checkout_success(request):
    domain = models.Domain.objects.get(pending=True)
    checkout = models.Checkout.objects.get(domain=domain)

    # register domain
    centralnic.register_domain(domain)

    # complete registration on success
    checkout.delete()
    domain.pending = False
    domain.save()

    # respond with message
    messages.success(request, "payment complete")
    return redirect("index")


def checkout_failure(request):
    # cleanup pending domain and checkout instances
    domain = models.Domain.objects.filter(pending=True)
    domain.delete()
    models.Checkout.objects.all().delete()

    # respond with message
    messages.error(request, "payment failed")
    return redirect("domain_create")
