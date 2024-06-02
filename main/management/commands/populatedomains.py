from django.core.management.base import BaseCommand

from main import centralnic, models


class Command(BaseCommand):
    help = "Populate domains from CentralNIC"

    def handle(self, *args, **options):
        domain_list = centralnic.get_domain_list()
        print(f"Domain list: {domain_list}")

        for domain_name in domain_list:
            domain_object = centralnic.get_domain_info(domain_name)
            contact = models.Contact.objects.get(api_id=domain_object["contact_api_id"])
            domain_instance = models.Domain(domain_name=domain_name, contact=contact)

            # nameservers
            for index, nameserver_value in enumerate(domain_object["nameserver_list"]):
                nameserver_key = f"nameserver{index}"
                setattr(domain_instance, nameserver_key, nameserver_value)
            domain_instance.save()
            print(f"Saved ID: {domain_instance}")
