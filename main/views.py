from django.shortcuts import render
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
            "domain_list": models.Domain.objects.all(),
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
    success_url = reverse_lazy("index")

    def form_valid(self, form):
        self.object = form.save(commit=False)
        centralnic.register_domain(self.object)
        return super().form_valid(form)
