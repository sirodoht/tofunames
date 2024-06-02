import logging
from django.core.management.base import BaseCommand

from main import centralnic, models

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Populate contacts from CentralNIC"

    def handle(self, *args, **options):
        contact_list = centralnic.get_contact_list()
        print(f"Contact list: {contact_list}")

        print("\nStored:")
        for contact_api_id in contact_list:
            contact_object = centralnic.get_contact_info(contact_api_id)
            contact = models.Contact.objects.create(**contact_object)
            print(f"ID: {contact}")
