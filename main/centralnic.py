import httpx
from django.conf import settings


BASE_URL = "https://api.rrpproxy.net/api/call.cgi"
USERNAME = settings.CENTRALNIC_USERNAME
PASSWORD = settings.CENTRALNIC_PASSWORD


def create_contact(contact):
    params = {
        "s_login": USERNAME,
        "s_pw": PASSWORD,
        "command": "AddContact",
        "firstname": contact.first_name,
        "lastname": contact.last_name,
        "street0": contact.street,
        "city": contact.city,
        "zip": contact.postal,
        "country": contact.country,
        "phone": contact.phone,
        "email": contact.email,
        # "x-whoisprivacy": "1",
        # "preverify=1",
        # "new=1",
    }
    req = httpx.get(BASE_URL, params=params)

    if req.status_code != 200:
        raise Exception("centralnic API for contact creation failed")

    # example of failure:
    #  [
    # 0:   '[RESPONSE]',
    # 1:   'code = 503',
    # 2:   'description = Invalid attribute name; X-WRONGARGUMENT',
    # 3:   'EOF',
    # 4:   ''
    #  ]
    # example of success:
    #  [
    # 0:    '[RESPONSE]',
    # 1:    'code = 200',
    # 2:    'description = Command completed successfully',
    # 3:    'queuetime = 0',
    # 4:    'runtime = 0.058',
    # 5:    'property[auth][0] = xxx',
    # 6:    'property[contact][0] = P-ACX100',
    # 7:    'property[created date][0] = 2024-06-02 15:45:55',
    # 8:    'property[roid][0] = 0_CONTACT-KEYSYS',
    # 9:    'property[validated][0] = 1',
    # 0:    'property[verified][0] = 1',
    # 1:    'EOF',
    # 2:    ''
    #  ]
    api_response = req.content.decode("utf-8")
    contact.api_log = api_response
    contact.save()

    # save API id on contact object separately
    api_response = api_response.split("\n")
    contact.api_id = api_response[6].split(" ")[2]
    contact.save()

    # check for errors
    if api_response[0] != "[RESPONSE]":
        raise Exception("centralnic API for contact creation unexpected error")
    if api_response[1] != "code = 200":
        raise Exception(f"centralnic API for contact creation error: {api_response[1]}")


def register_domain(domain):
    params = {
        "s_login": USERNAME,
        "s_pw": PASSWORD,
        "command": "AddDomain",
        "domain": domain.domain_name,
        "period": "1",
        "ownercontact0": domain.contact.api_id,
        "admincontact0": domain.contact.api_id,
        "techcontact0": domain.contact.api_id,
        "billingcontact0": domain.contact.api_id,
        "nameserver0": domain.nameserver0,
        "nameserver1": domain.nameserver1,
        "nameserver2": domain.nameserver2,
        "nameserver3": domain.nameserver3,
    }
    req = httpx.get(BASE_URL, params=params)

    if req.status_code != 200:
        raise Exception("centralnic API for domain creation failed")

    api_response = req.content.decode("utf-8")
    domain.api_log = api_response
    domain.save()

    # save API id on domain object separately
    api_response = api_response.split("\n")
    domain.api_id = api_response[6].split(" ")[2]
    domain.save()

    # check for errors
    if api_response[0] != "[RESPONSE]":
        raise Exception("centralnic API for domain creation unexpected error")
    if api_response[1] != "code = 200":
        raise Exception(f"centralnic API for domain creation error: {api_response[1]}")


def get_contact_list():
    params = {
        "s_login": USERNAME,
        "s_pw": PASSWORD,
        "command": "QueryContactList",
    }
    req = httpx.get(BASE_URL, params=params)

    if req.status_code != 200:
        raise Exception("centralnic API for contact list failed")

    api_response = req.content.decode("utf-8")
    api_response = api_response.split("\n")

    # check for errors
    if api_response[0] != "[RESPONSE]":
        raise Exception("centralnic API for contact list unexpected error")
    if api_response[1] != "code = 200":
        raise Exception(f"centralnic API for contact list error: {api_response[1]}")

    # parse
    contact_list = []
    for entry in api_response:
        key = "property[contact]"
        if len(entry) >= len(key) and entry[: len(key)] == key:
            contact_api_id = entry.split(" = ")[1]
            contact_list.append(contact_api_id)

    return contact_list


def get_contact_info(contact_api_id):
    params = {
        "s_login": USERNAME,
        "s_pw": PASSWORD,
        "command": "StatusContact",
        "contact": contact_api_id,
    }
    req = httpx.get(BASE_URL, params=params)

    if req.status_code != 200:
        raise Exception("centralnic API for contact status failed")

    api_response = req.content.decode("utf-8")
    api_response = api_response.split("\n")

    # check for errors
    if api_response[0] != "[RESPONSE]":
        raise Exception("centralnic API for domain status unexpected error")
    if api_response[1] != "code = 200":
        raise Exception(f"centralnic API for domain status error: {api_response[1]}")

    # parse
    contact_object = {}
    for entry in api_response:
        contact_object["api_id"] = contact_api_id
        api_property_names = {
            "first_name": "property[first name]",
            "last_name": "property[last name]",
            "email": "property[email]",
            "phone": "property[phone]",
            "street": "property[street]",
            "city": "property[city]",
            "postal": "property[zip]",
            "country": "property[country]",
        }
        for db_property, api_property in api_property_names.items():
            if (
                len(entry) >= len(api_property)
                and entry[: len(api_property)] == api_property
            ):
                contact_object[db_property] = entry.split(" = ")[1]

    return contact_object


def get_domain_list():
    params = {
        "s_login": USERNAME,
        "s_pw": PASSWORD,
        "command": "QueryDomainList",
    }
    req = httpx.get(BASE_URL, params=params)

    if req.status_code != 200:
        raise Exception("centralnic API for domain list failed")

    # example response:
    # [
    #     '[RESPONSE]',
    #     'code = 200',
    #     'description = Command completed successfully',
    #     'queuetime = 0',
    #     'runtime = 0.003',
    #     'property[column][0] = domain',
    #     'property[count][0] = 2',
    #     'property[domain][0] = oddbroccoli.com',
    #     'property[domain][1] = tofunames.com',
    #     'property[first][0] = 0',
    #     'property[last][0] = 1',
    #     'property[limit][0] = 1000',
    #     'property[total][0] = 2',
    #     'EOF',
    #     ''
    # ]
    api_response = req.content.decode("utf-8")
    api_response = api_response.split("\n")

    # check for errors
    if api_response[0] != "[RESPONSE]":
        raise Exception("centralnic API for domain list unexpected error")
    if api_response[1] != "code = 200":
        raise Exception(f"centralnic API for domain list error: {api_response[1]}")

    # parse domain names
    domain_list = []
    for entry in api_response:
        if len(entry) > 16 and entry[:16] == "property[domain]":
            domain_name = entry.split(" = ")[1]
            domain_list.append(domain_name)

    return domain_list


def get_domain_info(domain_name):
    params = {
        "s_login": USERNAME,
        "s_pw": PASSWORD,
        "command": "StatusDomain",
        "domain": domain_name,
    }
    req = httpx.get(BASE_URL, params=params)

    if req.status_code != 200:
        raise Exception("centralnic API for contact creation failed")

    # example response:
    # '[RESPONSE]',
    # 'code = 200',
    # 'description = Command completed successfully',
    # 'queuetime = 0',
    # 'runtime = 0.046',
    # 'property[created by][0] = sirodoht',
    # 'property[created date][0] = 2024-05-28 22:17:44.0',
    # 'property[updated by][0] = sirodoht',
    # 'property[updated date][0] = 2024-06-02 16:59:57.0',
    # 'property[registrar][0] = sirodoht',
    # 'property[registration expiration date][0] = 2025-05-28 22:17:44.0',
    # 'property[paiduntil date][0] = 2025-05-28 22:17:44.0',
    # 'property[renewal date][0] = 2025-07-02 22:17:44.0',
    # 'property[auth][0] = xxx',
    # 'property[renewalmode][0] = DEFAULT',
    # 'property[transfermode][0] = DEFAULT',
    # 'property[roid][0] = 0000_DOMAIN-KEYSYS',
    # 'property[domain][0] = tofunames.com',
    # 'property[domain idn][0] = tofunames.com',
    # 'property[zone][0] = com',
    # 'property[status][0] = ACTIVE',
    # 'property[rgp status][0] = addPeriod',
    # 'property[transfer lock][0] = 0',
    # 'property[nameserver][0] = NS1.DNSIMPLE.COM',
    # 'property[nameserver][1] = NS2.DNSIMPLE-EDGE.NET',
    # 'property[nameserver][2] = NS3.DNSIMPLE.COM',
    # 'property[nameserver][3] = NS4.DNSIMPLE-EDGE.ORG',
    # 'property[owner contact][0] = P-XXX000',
    # 'property[admin contact][0] = P-XXX000',
    # 'property[tech contact][0] = P-XXX000',
    # 'property[billing contact][0] = P-XXX000',
    # 'property[x-domain-roid][0] = 999_DOMAIN_COM-VRSN',
    # 'EOF',
    # ''
    api_response = req.content.decode("utf-8")
    api_response = api_response.split("\n")

    # check for errors
    if api_response[0] != "[RESPONSE]":
        raise Exception("centralnic API for domain creation unexpected error")
    if api_response[1] != "code = 200":
        raise Exception(f"centralnic API for domain creation error: {api_response[1]}")

    # parse
    domain_object = {
        "nameserver_list": [],
    }
    for entry in api_response:
        key = "property[nameserver]"
        if len(entry) >= len(key) and entry[: len(key)] == key:
            nameserver = entry.split(" = ")[1].lower()
            domain_object["nameserver_list"].append(nameserver)

        key = "property[owner contact][0]"
        if len(entry) >= len(key) and entry[: len(key)] == key:
            domain_object["contact_api_id"] = entry.split(" = ")[1]

    return domain_object
