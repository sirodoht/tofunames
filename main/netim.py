"""
Vendored from:
https://github.com/netim-com/netim-apirest-client-for-python
"""

import json
import httpx
import atexit
import os


class NetimAPIException(Exception):
    pass


class APIRest:
    """Constructor for class APIRest

    Args:
        userID (str): the ID the client uses to connect to his NETIM account.
        secret (str): the SECRET the client uses to connect to his NETIM account.

    """

    __connected = False
    __sessionID = None

    __userID = None
    __secret = None
    __apiURL = None
    __defaultLanguage = None

    __lastRequestParams = None
    __lastRequestRessource = None
    __lastHttpVerb = None
    __lastHttpStatus = None
    __lastResponse = None
    __lastError = None

    def __init__(self):
        atexit.register(self.__del__)

        self.__userID = os.environ.get("NETIM_USERID")
        self.__secret = os.environ.get("NETIM_SECRET")
        self.__apiURL = os.environ.get("NETIM_ENDPOINT")
        self.__defaultLanguage = "EN"

    def __del__(self):
        if self.__connected and self.__sessionID is not None:
            self.sessionClose()

    def __isSessionOpen(self, ressource: str, httpVerb: str):
        return "session" in ressource and httpVerb == "post"

    def __isSessionClose(self, ressource: str, httpVerb: str):
        return "session" in ressource and httpVerb == "delete"

    def call(self, ressource: str, httpVerb: str, params: dict = {}):
        """Launches a function of the API, abstracting the connect/disconnect part to one place

        Example 1: API command returning a StructOperationResponse

        return self.call("contacts/$idContactToDelete", {}, 'delete');

        Example 2: API command that takes many args
        params = {
            'host': host,
            'ipv4': ipv4,
            'ipv6': ipv6
        }
        return $this->call('/hosts', params, 'post');

        Args:
            ressource (str): name of a ressource in the API.
            params (dict): the parameters of ressource.
            httpVerb (str): the http verb for the request (get, post, put, patch, delete).

        Raises:
            NetimAPIException: if httpverb is wrong or an error described in the exception's message.

        Returns:
            dict: the result of the call of ressource with parameters param and http verb httpVerb.
        """
        httpVerb = httpVerb.lower()
        self.__lastRequestRessource = ressource
        self.__lastRequestParams = params
        self.__lastHttpVerb = httpVerb
        self.__lastHttpStatus = ""
        self.__lastResponse = ""
        self.__lastError = ""

        try:
            # login
            if not self.__connected:
                if self.__isSessionClose(ressource, httpVerb):
                    return
                elif not self.__isSessionOpen(ressource, httpVerb):
                    self.sessionOpen()
            elif self.__connected and self.__isSessionOpen(ressource, httpVerb):
                return

            # Call the REST ressource
            if self.__isSessionOpen(ressource, httpVerb):
                headers = {
                    "Accept-Language": self.__defaultLanguage,
                    "Content-Type": "application/json",
                }
                response = httpx.post(
                    self.__apiURL + "/session",
                    auth=(self.__userID, self.__secret),
                    headers=headers,
                )
            else:
                headers = {
                    "Authorization": "Bearer " + self.__sessionID,
                    "Content-type": "application/json",
                }
                function = getattr(httpx, httpVerb)
                response = function(
                    self.__apiURL + "/" + ressource,
                    headers=headers,
                    data=json.dumps(params),
                )
            self.__lastHttpStatus = response.status_code

            try:
                result = json.loads(response.text)
            except json.decoder.JSONDecodeError:
                raise NetimAPIException("Unknown error")

            if self.__isSessionClose(ressource, httpVerb):
                if response.status_code == 200:
                    self.__connected = False
                elif response.status_code == 401:
                    pass
                else:
                    raise NetimAPIException(result["message"])
            elif self.__isSessionOpen(ressource, httpVerb):
                if response.status_code == 200:
                    self.__sessionID = result["access_token"]
                    self.__connected = True
                else:
                    raise NetimAPIException(result["message"])
            else:
                # Code doesn't start with "2xx"
                if response.status_code < 200 or response.status_code > 299:
                    if response.status_code == 401:
                        self.__connected = False
                    if "message" in result:
                        raise NetimAPIException(result["message"])
                    else:
                        raise NetimAPIException("")

            self.__lastResponse = result
        except NetimAPIException as exception:
            self.__lastError = str(exception)
            raise exception

        return result

    """
    GETTER
    """

    def getLastRequestParams(self):
        return self.__lastRequestParams

    def getLastRequestRessource(self):
        return self.__lastRequestRessource

    def getLastHttpVerb(self):
        return self.__lastHttpVerb

    def getLastHttpStatus(self):
        return self.__lastHttpStatus

    def getLastResponse(self):
        return self.__lastResponse

    def getLastError(self):
        return self.__lastError

    """
    API FUNCTIONS
    """

    def sessionOpen(self) -> None:
        """Opens a session with REST

        Raises:
            NetimAPIException: if failed to connect.
        """
        self.call("session", "post")

    def sessionClose(self) -> None:
        if self.__connected and self.__sessionID is not None:
            self.call("session", "delete")
            if self.__lastHttpStatus != 200:
                raise NetimAPIException(self.__lastError)
            else:
                self.__sessionID = None
        self.__connected = False

    def sessionInfo(self) -> dict:
        """Return the information of the current session.

        Raises:
            NetimAPIException: if user is not connected.

        Returns:
            dict: A structure StructSessionInfo

        See:
            sessionInfo API https://support.netim.com/en/wiki/SessionInfo

        """
        if not self.__connected:
            raise NetimAPIException("Not connected")
        return self.call("session/", "get")

    def queryAllSessions(self) -> list:
        """Returns all active sessions linked to the reseller account.

        Returns:
            dict: a dictionary of StructSessionInfo.

        See:
            queryAllSessions API https://support.netim.com/en/wiki/QueryAllSessions
        """
        return self.call("sessions/", "get")

    def sessionSetPreference(self, type: str, value: str) -> None:
        """Updates the settings of the current session.

        Args:
            type (str): Setting to be modified ('lang','sync')
            value (str): New value of the Setting (lang: 'EN';'FR',sync:'0'(for asynchronous);'1'(for synchronous)).
        """
        self.call("session/", "patch", {"type": type, "value": value})

    def hello(self) -> str:
        """Returns a welcome message

                Raises:
            NetimAPIException:

        Returns:
            str: string a welcome message

        See:
            hello API http://support.netim.com/en/wiki/Hello
        """

        return self.call("hello/", "get")

    def queryResellerAccount(self) -> dict:
        """Returns the list of parameters reseller account

        Returns:
            str: list of parameters reseller account
        """
        return self.call("account/", "get")

    def contactCreate(self, contact: dict) -> dict:
        """Creates a contact

        Args:
            contact (Contact): the contact to create

        Returns:
            str: the ID of the contact

        See:
            contactCreate API http://support.netim.com/en/wiki/ContactCreate
            StructContact: http://support.netim.com/en/wiki/StructContact
        """

        params = {"contact": contact}
        return self.call("contact/", "post", params)

    def contactInfo(self, id: str) -> dict:
        """Returns all informations about a contact object

        Args:
            id (str): ID of the contact to be queried

        Returns:
            Contact: information on the contact
        See:
            contactInfo API http://support.netim.com/en/wiki/ContactInfo
            StructContactReturn API http://support.netim.com/en/wiki/StructContactReturn
        """

        return self.call("contact/" + id, "get")

    def contactUpdate(self, id: str, contact: dict) -> dict:
        """Edit contact details

        Args:
            id (str): the ID of the contact to be updated
            contact (Contact): the contact object containing the new values

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            contactUpdate API http://support.netim.com/en/wiki/ContactUpdate
        """

        params = {"contact": contact}
        return self.call("contact/" + id, "patch", params)

    def contactDelete(self, id: str) -> dict:
        """Deletes a contact object

        Args:
            id (str): ID of the contact to be deleted

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            contactDelete API http://support.netim.com/en/wiki/ContactDelete
            StructOperationResponse API http://support.netim.com/en/wiki/StructOperationResponse
        """

        return self.call("contact/" + id, "delete")

    def queryOpe(self, id: str) -> dict:
        """Query informations about the state of an operation

        Args:
            id (str): The id of the operation requested

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            queryOpe API http://support.netim.com/en/wiki/QueryOpe
        """

        return self.call("operation/" + id, "get")

    def cancelOpe(self, id: str) -> None:
        """Cancel a pending operation

        Warning:
            Depending on the current status of the operation, the cancellation might not be possible

        Args:
            id (str): Tracking ID of the operation

        Throws:
            NetimAPIException

        See:
            cancelOpe http://support.netim.com/en/wiki/CancelOpe
        """

        self.call("operation/" + id + "/cancel/", "patch")

    def queryOpeList(self, tld: str) -> dict:
        """Returns the status (opened/closed) for all operations for the extension

        Args:
            tld (str): Extension (uppercase without dot)

        Returns:
            dict: A dictionary with (Name of the operation, boolean active)

        Throws:
            NetimAPIException

        See:
            queryOpeList API https://support.netim.com/en/wiki/QueryOpeList
        """
        return self.call("tld/" + tld + "/operations/", "get")

    def queryOpePending(self) -> list:
        """Returns the list of pending operations processing

        Returns:
            StructQueryOpePending[]: the list of pending operations processing

        Throws:
            NetimAPIException

        See:
            queryOpePending API https://support.netim.com/en/wiki/QueryOpePending
        """
        return self.call("operations/pending/", "get")

    def queryContactList(self, filter: str = "", field: str = "") -> list:
        """Returns all contacts linked to the reseller account.

        Args:
            filter (str): The filter applies on the "field"
            field (str): idContact / firstName / lastName / bodyForm / isOwner

        Returns:
            StructContactList[]: An array of StructContactList

        Throws:
            NetimAPIException

        See:
            queryContactList API https://support.netim.com/en/wiki/QueryContactList
        """
        if not filter and not field:
            return self.call("contacts/", "get")
        else:
            return self.call("contacts/" + field + "/" + filter + "/", "get")

    def hostCreate(self, host: str, ipv4: list, ipv6: list) -> dict:
        """Creates a new host at the registry

        Args:
            host (str): hostname
            ipv4 (list): Must contain ipv4 adresses as strings
            ipv6 (list): Must contain ipv6 adresses as strings

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            hostCreate API https://support.netim.com/en/wiki/HostCreate
        """
        params = {
            "host": host,
            "ipv4": ipv4,
            "ipv6": ipv6,
        }
        return self.call("host/", "post", params)

    def hostDelete(self, host: str) -> dict:
        """Deletes an Host at the registry

        Args:
            host (str): hostname to be deleted

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            hostDelete API https://support.netim.com/en/wiki/HostDelete
        """
        return self.call("host/" + host, "delete")

    def hostUpdate(self, host: str, ipv4: list, ipv6: list) -> dict:
        """Updates a host at the registry

        Args:
            host (str): hostname
            ipv4 (list): Must contain ipv4 adresses as strings
            ipv6 (list): Must contain ipv6 adresses as strings

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            hostUpdate API http://support.netim.com/en/wiki/HostUpdate
        """
        params = {
            "ipv4": ipv4,
            "ipv6": ipv6,
        }
        return self.call("host/" + host, "patch", params)

    def queryHostList(self, filter: str) -> list:
        """Returns all hosts linked to the reseller account.

        Args:
            filter (str): The filter applies onto the host name

        Returns:
            StructHostList[]: a list of StructHostList

        Throws:
            NetimAPIException

        See:
            queryHostList API http://support.netim.com/en/wiki/QueryHostList
        """
        return self.call("hosts/" + filter, "get")

    def domainCheck(self, domain: str) -> list:
        """Checks if domain names are available for registration

        Args:
            domain (str): Domain names to be checked
                                You can provide several domain names separated with semicolons.
                        Caution :
                            - you can't mix different extensions during the same call
                            - all the extensions don't accept a multiple checkDomain. See HasMultipleCheck in Category:Tld
        Returns:
            StructDomainCheckResponse[]: a list of StructDomainCheckResponse
        Throws:
            NetimAPIException
        See:
            DomainCheck API http://support.netim.com/en/wiki/DomainCheck
            StructDomainCheckResponse http://support.netim.com/en/wiki/StructDomainCheckResponse
        """

        domain = domain.lower()

        return self.call("domain/" + domain + "/check/", "get")

    def domainCreate(
        self,
        domain: str,
        idOwner: str,
        idAdmin: str,
        idTech: str,
        idBilling: str,
        ns1: str,
        ns2: str,
        ns3: str,
        ns4: str,
        ns5: str,
        duration: int,
        templateDNS: int = None,
    ) -> dict:
        """Requests a new domain registration

        Args:
            domain (str): the name of the domain to create
            idOwner (str): the id of the owner for the new domain
            idAdmin (str): the id of the admin for the new domain
            idTech (str): the id of the tech for the new domain
            idBilling (str): the id of the billing for the new domain
            ns1 (str): the name of the first dns
            ns2 (str): the name of the second dns
            ns3 (str): the name of the third dns
            ns4 (str): the name of the fourth dns
            ns5 (str): the name of the fifth dns
            duration (int): how long the domain will be created
            templateDNS (int, optional): number of the template DNS created on netim.com/direct. Defaults to None.

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            domainCreate API http://support.netim.com/en/wiki/DomainCreate
        """
        domain = domain.lower()

        params = {
            "idOwner": idOwner,
            "idAdmin": idAdmin,
            "idTech": idTech,
            "idBilling": idBilling,
            "ns1": ns1,
            "ns2": ns2,
            "ns3": ns3,
            "ns4": ns4,
            "ns5": ns5,
            "duration": duration,
        }

        if templateDNS is not None:
            params["templateDNS"] = templateDNS

        return self.call("domain/" + domain + "/", "post", params)

    def domainInfo(self, domain: str) -> dict:
        """Returns all informations about a domain name

        Args:
            domain (str): name of the domain

        Returns:
            StructDomainInfo: information about the domain

        See:
            domainInfo API http://support.netim.com/en/wiki/DomainInfo
        """

        domain = domain.lower()

        return self.call("domain/" + domain + "/info/", "get")

    def domainCreateLP(
        self,
        domain: str,
        idOwner: str,
        idAdmin: str,
        idTech: str,
        idBilling: str,
        ns1: str,
        ns2: str,
        ns3: str,
        ns4: str,
        ns5: str,
        duration: int,
        launchPhase: str,
    ) -> dict:
        """Requests a new domain registration

        Args:
            domain (str): the name of the domain to create
            idOwner (str): the id of the owner for the new domain
            idAdmin (str): the id of the admin for the new domain
            idTech (str): the id of the tech for the new domain
            idBilling (str): the id of the billing for the new domain
            ns1 (str): the name of the first dns
            ns2 (str): the name of the second dns
            ns3 (str): the name of the third dns
            ns4 (str): the name of the fourth dns
            ns5 (str): the name of the fifth dns
            duration (int): how long the domain will be created
            launchPhase (str): Code of the launch period.

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            domainCreate API http://support.netim.com/en/wiki/DomainCreateLP
        """
        domain = domain.lower()

        params = {
            "idOwner": idOwner,
            "idAdmin": idAdmin,
            "idTech": idTech,
            "idBilling": idBilling,
            "ns1": ns1,
            "ns2": ns2,
            "ns3": ns3,
            "ns4": ns4,
            "ns5": ns5,
            "duration": duration,
            "launchPhase": launchPhase,
        }

        return self.call("domain/" + domain + "/lp/", "post", params)

    def domainDelete(self, domain: str, typeDelete: str = "NOW") -> dict:
        """Deletes immediately a domain name

        Args:
            domain (str): the name of the domain to delete
            typeDelete (str, optional): if the deletion is to be done now or not. Only supported value as of 2.0 is 'NOW'. Defaults to 'NOW'.

        Returns:
            StructOperationResponse: giving information on the status of the operation

        Throws:
            NetimAPIException

        See:
            domainDelete API http://support.netim.com/en/wiki/DomainDelete
        """

        domain = domain.lower()

        params = {"typeDelete": typeDelete.upper()}

        return self.call("domain/" + domain + "/", "delete", params)

    def domainTransferIn(
        self,
        domain: str,
        authID: str,
        idOwner: str,
        idAdmin: str,
        idTech: str,
        idBilling: str,
        ns1: str,
        ns2: str,
        ns3: str,
        ns4: str,
        ns5: str,
    ) -> dict:
        """Requests the transfer of a domain name to Netim

        Args:
            domain (str): name of the domain to transfer
            authID (str): authorisation code / EPP code (if applicable)
            idOwner (str): a valid idOwner. Can also be #AUTO#
            idAdmin (str): a valid idAdmin
            idTech (str): a valid idTech
            idBilling (str): a valid idBilling
            ns1 (str): the name of the first dns
            ns2 (str): the name of the second dns
            ns3 (str): the name of the third dns
            ns4 (str): the name of the fourth dns
            ns5 (str): the name of the fifth dns

        Throws:
            NetimAPIException

        See:
            domainTransferIn API http://support.netim.com/en/wiki/DomainTransferIn

        Returns:
            StructOperationResponse: giving information on the status of the operation
        """

        domain = domain.lower()

        params = {
            "authID": authID,
            "idOwner": idOwner,
            "idAdmin": idAdmin,
            "idTech": idTech,
            "idBilling": idBilling,
            "ns1": ns1,
            "ns2": ns2,
            "ns3": ns3,
            "ns4": ns4,
            "ns5": ns5,
        }

        return self.call("domain/" + domain + "/transfer/", "post", params)

    def domainTransferTrade(
        self,
        domain: str,
        authID: str,
        idOwner: str,
        idAdmin: str,
        idTech: str,
        idBilling: str,
        ns1: str,
        ns2: str,
        ns3: str,
        ns4: str,
        ns5: str,
    ) -> dict:
        """Requests the transfer (with change of domain holder) of a domain name to Netim

        Args:
            domain (str): name of the domain to transfer
            authID (str): authorisation code / EPP code (if applicable)
            idOwner (str): a valid idOwner
            idAdmin (str): a valid idAdmin
            idTech (str): a valid idTech
            idBilling (str): a valid idBilling
            ns1 (str): the name of the first dns
            ns2 (str): the name of the second dns
            ns3 (str): the name of the third dns
            ns4 (str): the name of the fourth dns
            ns5 (str): the name of the fifth dns

        Throws:
            NetimAPIException

        See:
            domainTransferIn API http://support.netim.com/en/wiki/DomainTransferTrade

        Returns:
            StructOperationResponse: giving information on the status of the operation
        """

        domain = domain.lower()

        params = {
            "authID": authID,
            "idOwner": idOwner,
            "idAdmin": idAdmin,
            "idTech": idTech,
            "idBilling": idBilling,
            "ns1": ns1,
            "ns2": ns2,
            "ns3": ns3,
            "ns4": ns4,
            "ns5": ns5,
        }

        return self.call("domain/" + domain + "/transfer-trade/", "post", params)

    def domainInternalTransfer(
        self,
        domain: str,
        authID: str,
        idAdmin: str,
        idTech: str,
        idBilling: str,
        ns1: str,
        ns2: str,
        ns3: str,
        ns4: str,
        ns5: str,
    ) -> dict:
        """Requests the transfer (with change of domain holder) of a domain name to Netim

        Args:
            domain (str): name of the domain to transfer
            authID (str): authorisation code / EPP code (if applicable)
            idAdmin (str): a valid idAdmin
            idTech (str): a valid idTech
            idBilling (str): a valid idBilling
            ns1 (str): the name of the first dns
            ns2 (str): the name of the second dns
            ns3 (str): the name of the third dns
            ns4 (str): the name of the fourth dns
            ns5 (str): the name of the fifth dns

        Throws:
            NetimAPIException

        See:
            domainTransferIn API http://support.netim.com/en/wiki/DomainInternalTransfer

        Returns:
            StructOperationResponse: giving information on the status of the operation
        """
        domain = domain.lower()

        params = {
            "authID": authID,
            "idAdmin": idAdmin,
            "idTech": idTech,
            "idBilling": idBilling,
            "ns1": ns1,
            "ns2": ns2,
            "ns3": ns3,
            "ns4": ns4,
            "ns5": ns5,
        }

        return self.call("domain/" + domain + "/internal-transfer/", "patch", params)

    def domainRenew(self, domain: str, duration: int) -> dict:
        """Renew a domain name for a new subscription period

        Args:
            domain (str): the name of the domain to renew
            duration (int): the duration of the renewal expressed in year. Must be at least 1 and less than the maximum amount

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainRenew API  http://support.netim.com/en/wiki/DomainRenew
        """
        domain = domain.lower()
        params = {"duration": str(duration)}

        return self.call("domain/" + domain + "/renew/", "patch", params)

    def domainRestore(self, domain: str) -> dict:
        """Restores a domain name in quarantine / redemption status

        Args:
            domain (str): name of the domain

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainRenew API  http://support.netim.com/en/wiki/DomainRenew
        """
        domain = domain.lower()
        return self.call("domain/" + domain + "/restore/", "patch")

    def domainSetPreference(self, domain: str, codePref: str, value: str) -> dict:
        """Updates the settings of a domain name

        Args:
            domain (str): name of the domain
            codePref (str): setting to be modified. Accepted value are 'whois_privacy', 'registrar_lock', 'auto_renew', 'tag' or 'note'
            value (str): new value for the settings.

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainSetPreference API  http://support.netim.com/en/wiki/DomainSetPreference
        """
        domain = domain.lower()

        params = {"codePref": codePref, "value": value}

        return self.call("domain/" + domain + "/preference/", "patch", params)

    def domainTransferOwner(self, domain: str, idOwner: str) -> dict:
        """Requests the transfer of the ownership to another party

        Args:
            domain (str): name of the domain
            idOwner (str): id of the new owner

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainTransferOwner API http://support.netim.com/en/wiki/DomainTransferOwner
        """
        domain = domain.lower()

        params = {"idOwner": idOwner}

        return self.call("domain/" + domain + "/transfer-owner/", "put", params)

    def domainChangeContact(
        self, domain: str, idAdmin: str, idTech: str, idBilling: str
    ) -> dict:
        """Replaces the contacts of the domain (administrative, technical, billing)

        Args:
            domain (str): name of the domain
            idAdmin (str):  id of the admin contact
            idTech (str):  id of the tech contact
            idBilling (str):  id of the billing contact

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainChangeContact API http://support.netim.com/en/wiki/DomainChangeContact
        """
        domain = domain.lower()

        params = {"idAdmin": idAdmin, "idTech": idTech, "idBilling": idBilling}

        return self.call("domain/" + domain + "/contacts/", "put", params)

    def domainChangeDNS(
        self, domain: str, ns1: str, ns2: str, ns3: str, ns4: str, ns5: str
    ) -> dict:
        """Replaces the DNS servers of the domain (redelegation)

        Args:
            domain (str): name of the domain
            ns1 (str): the name of the first dns
            ns2 (str): name of the second dns
            ns3 (str): name of the third dns
            ns4 (str): name of the fourth dns
            ns5 (str): name of the fifth dns

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainChangeDNS API http://support.netim.com/en/wiki/DomainChangeDNS
        """
        domain = domain.lower()

        params = {"ns1": ns1, "ns2": ns2, "ns3": ns3, "ns4": ns4, "ns5": ns5}

        return self.call("domain/" + domain + "/dns/", "put", params)

    def domainSetDNSSec(self, domain: str, enable: int) -> dict:
        """Allows to sign a domain name with DNSSEC if it uses NETIM DNS servers

        Args:
            domain (str): name of the domain
            enable (int): New signature value 0 : unsign 1 : sign

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainSetDNSsec API http://support.netim.com/en/wiki/DomainSetDNSsec
        """
        domain = domain.lower()
        params = {"enable": enable}
        return self.call("domain/" + domain + "/dnssec/", "patch", params)

    def domainAuthID(self, domain: str, sendToRegistrant: int) -> dict:
        """Returns the authorization code to transfer the domain name to another registrar or to another client account

        Args:
            domain (str): name of the domain to get the AuthID
            sendToRegistrant (int): recipient of the AuthID. Possible value are 0 for the reseller and 1 for the registrant

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainSetDNSsec API http://support.netim.com/en/wiki/DomainSetDNSsec
        """
        domain = domain.lower()

        params = {"sendtoregistrant": sendToRegistrant}
        return self.call("domain/" + domain + "/authid/", "patch", params)

    def domainRelease(self, domain: str) -> dict:
        """Release a domain name (managed by the reseller) to its registrant (who will become a direct customer at Netim)

        Args:
            domain (str): domain name to be released

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainRelease API http://support.netim.com/en/wiki/DomainRelease
        """

        domain = domain.lower()

        return self.call("domain/" + domain + "/release/", "patch")

    def domainSetMembership(self, domain: str, token: str) -> dict:
        """Adds a membership to the domain name

        Args:
            domain (str): name of domain
            token (str): membership number into the community

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainSetMembership API http://support.netim.com/en/wiki/DomainSetMembership
        """
        domain = domain.lower()

        params = {"token": token}
        return self.call("/domain/" + domain + "/membership/", "patch", params)

    def domainTldInfo(self, tld: str) -> dict:
        """Returns all available operations for a given TLD

        Args:
            tld (str): a valid tld without the dot before it

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainTldInfo API http://support.netim.com/en/wiki/DomainTldInfo
        """
        return self.call("/tld/" + tld + "/", "get")

    def domainSetDNSSecExt(
        self,
        domain: str,
        DSRecords: list,
        flags: int,
        protocol: int,
        algo: int,
        pubKey: str,
    ) -> dict:
        """Allows to sign a domain name with DNSSEC if it doesn't use NETIM DNS servers

        Args:
            domain (str): name of the domain
            DSRecords (list): A StructDSRecord object
            flags (int):
            protocol (int):
            algo (int):
            pubKey (str):

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainSetDNSSecExt API http://support.netim.com/en/wiki/DomainSetDNSSecExt
        """
        domain = domain.lower()

        params = {
            "DSRecords": DSRecords,
            "flags": flags,
            "protocol": protocol,
            "algo": algo,
            "pubKey": pubKey,
        }

        return self.call("/domain/" + domain + "/dnssec/", "patch", params)

    def domainWhois(self, domain: str) -> str:
        """Returns whois informations on given domain

        Args:
            domain (str): the domain's name

        Throws:
            NetimAPIException

        Returns:
            str: information about the domain
        """
        domain = domain.lower()
        return self.call("/domain/" + domain + "/whois/", "get")

    def domainPriceList(self) -> dict:
        """Returns the list of all prices for each tld

        Throws:
            NetimAPIException

        Returns:
            StructDomainPriceList[]: An array of StructDomainPriceList

        See:
            domainPriceList API http://support.netim.com/en/wiki/DomainPriceList
        """
        return self.call("/tlds/price-list/", "get")

    def queryDomainPrice(self, domain: str, authID: str = "") -> dict:
        """Allows to know a domain's price

        Args:
            domain (str): name of domain
            authID (str, optional): authorisation code. Defaults to "".

        Throws:
            NetimAPIException

        Returns:
            StructQueryDomainPrice: An object StructQueryDomainPrice containing information about a domain's price

        See:
            queryDomainPrice API http://support.netim.com/en/wiki/QueryDomainPrice
        """
        domain = domain.lower()
        if authID:
            params = {"authId": authID}
            return self.call("/domain/" + domain + "/price/", "get", params)
        else:
            return self.call("/domain/" + domain + "/price/", "get")

    def queryDomainClaim(self, domain: str) -> int:
        """Allows to know if there is a claim on the domain name

        Args:
            domain (str): name of domain

        Throws:
            NetimAPIException

        Returns:
            int: 0 = no claim ; 1 = at least one claim

        See:
            queryDomainPrice API http://support.netim.com/en/wiki/QueryDomainPrice
        """
        domain = domain.lower()
        return self.call("/domain/" + domain + "/claim/", "get")

    def queryDomainList(self, filter: str) -> list:
        """Returns all domains linked to the reseller account.

        Args:
            filter (str): Domain name filter

        Throws:
            NetimAPIException

        Returns:
            StructDomainList[]: An array of StructDomainList

        See:
            queryDomainList API http://support.netim.com/en/wiki/QueryDomainList
        """
        return self.call("/domains/" + filter, "get")

    def domainZoneInit(self, domain: str, numTemplate: int) -> dict:
        """Resets all DNS settings from a template

        Args:
            domain (str): Domain name
            numTemplate (int): Template number

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainZoneInit API http://support.netim.com/en/wiki/DomainZoneInit
        """
        domain = domain.lower()

        params = {"numTemplate": numTemplate}

        return self.call("/domain/" + domain + "/zone/init/", "patch", params)

    def domainZoneCreate(
        self, domain: str, subdomain: str, type: str, value: str, options: dict
    ) -> dict:
        """Creates a DNS record into the domain zonefile

        Args:
            domain (str): name of the domain
            subdomain (str): subdomain
            type (str): type of DNS record. Accepted values are: 'A', 'AAAA', 'MX, 'CNAME', 'TXT', 'NS and 'SRV'
            value (str): value of the new DNS record
            options (dict): contains multiple StructOptionsZone : settings of the new DNS record

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainZoneCreate API http://support.netim.com/en/wiki/DomainZoneCreate
            StructOptionsZone http://support.netim.com/en/wiki/StructOptionsZone
        """
        domain = domain.lower()
        params = {
            "subdomain": subdomain,
            "type": type,
            "value": value,
            "options": options,
        }

        return self.call("/domain/" + domain + "/zone/", "post", params)

    def domainZoneDelete(
        self, domain: str, subdomain: str, type: str, value: str
    ) -> dict:
        """Deletes a DNS record into the domain's zonefile

        Args:
            domain (str): name of the domain
            subdomain (str): subdomain
            type (str): type of DNS record. Accepted values are: 'A', 'AAAA', 'MX', 'CNAME', 'TXT', 'NS' and 'SRV'
            value (str): value of the new DNS record

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainZoneDelete API http://support.netim.com/en/wiki/DomainZoneDelete
        """
        domain = domain.lower()
        params = {
            "subdomain": subdomain,
            "type": type,
            "value": value,
        }

        return self.call("/domain/" + domain + "/zone/", "delete", params)

    def domainZoneInitSoa(
        self,
        domain: str,
        ttl: int,
        ttlUnit: chr,
        refresh: int,
        refreshUnit: chr,
        retry: int,
        retryUnit: chr,
        expire: int,
        expireUnit: chr,
        minimum: int,
        minimumUnit: chr,
    ) -> dict:
        """Resets the SOA record of a domain name

        Args:
           domain (str): name of the domain
           ttl (int): time to live
           ttlUnit (chr): TTL unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
           refresh (int): Refresh delay
           refreshUnit (chr): Refresh unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
           retry (int): Retry delay
           retryUnit (chr): Retry unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
           expire (int): Expire delay
           expireUnit (chr): Expire unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
           minimum (int): Minimum delay
           minimumUnit (chr): Minimum unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainZoneDelete API http://support.netim.com/en/wiki/DomainZoneDelete
        """
        domain = domain.lower()
        params = {
            "ttl": ttl,
            "ttlUnit": ttlUnit,
            "refresh": refresh,
            "refreshUnit": refreshUnit,
            "retry": retry,
            "retryUnit": retryUnit,
            "expire": expire,
            "expireUnit": expireUnit,
            "minimumUnit": minimumUnit,
            "minimum": minimum,
        }

        return self.call("/domain/" + domain + "/zone/init-soa/", "patch", params)

    def queryZoneList(self, domain: str) -> list:
        """Returns all DNS records of a domain name

        Args:
            domain (str): Domain name

        Throws:
            NetimAPIException

        Returns:
            StructQueryZoneList[]: A list of StructQueryZoneList

        See:
            queryZoneList API http://support.netim.com/en/wiki/QueryZoneList
        """
        domain = domain.lower()

        return self.call("/domain/" + domain + "/zone/", "get")

    def domainMailFwdCreate(self, mailBox: str, recipients: str) -> dict:
        """Creates an email address forwarded to recipients

        Args:
            mailBox (str): email adress (or * for a catch-all)
            recipients (str): list of email adresses (separated by commas)

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainMailFwdCreate API http://support.netim.com/en/wiki/DomainMailFwdCreate
        """
        mailBox = mailBox.lower()
        params = {
            "recipients": recipients,
        }
        return self.call("/domain/" + mailBox + "/mail-forwarding/", "post", params)

    def domainMailFwdDelete(self, mailBox: str) -> dict:
        """Deletes an email forward

        Args:
            mailBox (str): email adress

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainMailFwdDelete API http://support.netim.com/en/wiki/DomainMailFwdDelete
        """
        mailBox = mailBox.lower()
        return self.call("/domain/" + mailBox + "/mail-forwarding/", "delete")

    def queryMailFwdList(self, domain: str) -> list:
        """Returns all email forwards for a domain name

        Args:
            domain (str): Domain name

        Throws:
            NetimAPIException

        Returns:
            StructQueryMailFwdList[]: A list of StructQueryMailFwdList

        See:
            queryMailFwdList API http://support.netim.com/en/wiki/QueryMailFwdList
        """
        domain = domain.lower()
        return self.call("/domain/" + domain + "/mail-forwardings/", "get")

    def domainWebFwdCreate(
        self, fqdn: str, target: str, type: str, options: dict
    ) -> dict:
        """Creates a web forwarding

        Args:
            fqdn (str): hostname (fully qualified domain name)
            target (str): target of the web forwarding
            type (str): type of the web forwarding. Accepted values are: "DIRECT", "IP", "MASKED" or "PARKING"
            options (dict): contains StructOptionsFwd : settings of the web forwarding. An array with keys: header, protocol, title and parking.

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainWebFwdCreate API http://support.netim.com/en/wiki/DomainWebFwdCreate
            StructOptionsFwd http://support.netim.com/en/wiki/StructOptionsFwd
        """
        params = {
            "target": target,
            "type": type.upper(),
            "options": options,
        }

        return self.call("/domain/" + fqdn + "/web-forwarding/", "post", params)

    def domainWebFwdDelete(self, fqdn: str) -> dict:
        """Removes a web forwarding

        Args:
            fqdn (str): hostname, a fully qualified domain name

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            domainWebFwdDelete API http://support.netim.com/en/wiki/DomainWebFwdDelete
        """
        return self.call("/domain/" + fqdn + "/web-forwarding/", "delete")

    def queryWebFwdList(self, domain: str) -> list:
        """Return all web forwarding of a domain name

        Args:
            domain (str): Domain name

        Throws:
            NetimAPIException

        Returns:
            StructQueryWebFwdList[]: A list of StructQueryWebFwdList

        See:
            domainWebFwdDelete API http://support.netim.com/en/wiki/QueryWebFwdList
            StructQueryWebFwdList https://support.netim.com/fr/wiki/StructQueryWebFwdList
        """
        domain = domain.lower()
        return self.call("/domain/" + domain + "/web-forwardings/", "get")

    def sslCreate(
        self, prod: str, duration: int, CSRInfo: dict, validation: str
    ) -> dict:
        """Creates a SSL redirection

        Args:
            prod (str): certificate type
            duration (int): period of validity (in years)
            CSRInfo (dict): containing informations about the CSR
            validation (str): validation method of the CSR (either by email or file) :
                "file"
                        "email:admin@yourdomain.com"
                        "email:postmaster@yourdomain.com,webmaster@yourdomain.com"

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            sslCreate API http://support.netim.com/en/wiki/SslCreate
            StructCSR https://support.netim.com/fr/wiki/StructCSR
        """
        params = {
            "prod": prod,
            "duration": duration,
            "CSR": CSRInfo,
            "validation": validation,
        }

        return self.call("/ssl/", "post", params)

    def sslRenew(self, IDSSL: str, duration: int) -> dict:
        """Renew a SSL certificate for a new subscription period.

        Args:
            IDSSL (str): SSL certificate ID
            duration (int): period of validity after the renewal (in years). Only the value 1 is valid

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            sslRenew API http://support.netim.com/en/wiki/SslRenew
        """
        params = {"duration": duration}

        return self.call("/ssl/" + IDSSL + "/renew/", "patch", params)

    def sslRevoke(self, IDSSL: str) -> dict:
        """Revokes a SSL Certificate.

        Args:
            IDSSL (str): SSL certificate ID

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            sslRenew API http://support.netim.com/en/wiki/SslRenew
        """
        return self.call("/ssl/" + IDSSL + "/", "delete")

    def sslReIssue(self, IDSSL: str, CSRInfo: dict, validation: str) -> dict:
        """Reissues a SSL Certificate.

        Args:
            IDSSL (str): SSL certificate ID
            CSRInfo (dict): Object containing informations about the CSR
            validation (str): validation method of the CSR (either by email or file) :
                "file"
                "email:admin@yourdomain.com"
                "email:postmaster@yourdomain.com,webmaster@yourdomain.com"

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            sslCreate API http://support.netim.com/en/wiki/SslCreate
            StructCSR https://support.netim.com/fr/wiki/StructCSR
        """
        params = {
            "CSR": CSRInfo,
            "validation": validation,
        }

        return self.call("/ssl/" + IDSSL + "/reissue/", "patch", params)

    def sslSetPreference(self, IDSSL: str, codePref: str, value: str) -> dict:
        """Updates the settings of a SSL certificate. Currently, only the autorenew setting can be modified.

        Args:
            IDSSL (str): SSL certificate ID
            codePref (str): Setting to be modified (auto_renew/to_be_renewed)
            value (str): New value of the setting

        Throws:
            NetimAPIException

        Returns:
            StructOperationResponse: giving information on the status of the operation

        See:
            sslSetPreference API http://support.netim.com/en/wiki/SslSetPreference
        """
        params = {
            "codePref": codePref,
            "value": value,
        }

        return self.call("/ssl/" + IDSSL + "/preference/", "patch", params)

    def sslInfo(self, IDSSL: str) -> dict:
        """Returns all the informations about a SSL certificate

        Args:
            IDSSL (str): SSL certificate ID

        Throws:
            NetimAPIException

        Returns:
            StructSSLInfo: containing the SSL certificate informations

        See:
            sslInfo API http://support.netim.com/en/wiki/SslInfo
        """
        return self.call("/ssl/" + IDSSL + "/", "get")

    def webHostingCreate(
        self, fqdn: str, offer: str, duration: int, cms: dict = {}
    ) -> dict:
        """Creates a web hosting

        Args:
            fqdn (str): Fully qualified domain of the main vhost. Warning, the secondary vhosts will always be subdomains of this FQDN
            offer (str): ID_TYPE_PROD of the hosting
            duration (int):
            cms (dict):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "fqdn": fqdn,
            "offer": offer,
            "duration": duration,
            "cms": cms,
        }

        return self.call("/webhosting/", "post", params)

    def webHostingGetID(self, fqdn: str) -> str:
        """Get the unique ID of the hosting

        Args:
            fqdn (str): [Fully qualified domain of the main vhost.

        Throws:
            NetimAPIException

        Returns:
            str: the unique ID of the hosting
        """
        return self.call("/webhosting/get-id/" + fqdn, "get")

    def webHostingInfo(self, id: str, additionalData: list) -> dict:
        """Get informations about web hosting (generic infos, MUTU platform infos, ISPConfig ...)

        Args:
            id (str): Hosting id
            additionalData (list): determines which infos should be returned ("NONE", "ALL", "WEB", "VHOSTS", "SSL_CERTIFICATES",
            "PROTECTED_DIRECTORIES", "DATABASES", "DATABASE_USERS", "FTP_USERS", "CRON_TASKS", "MAIL", "DOMAIN_MAIL")

        Throws:
            NetimAPIException

        Returns:
            dict: StructWebHostingInfo giving informations of the webhosting
        """
        params = {
            "additionalData": additionalData,
        }

        return self.call("/webhosting/" + id, "get", params)

    def webHostingRenew(self, id: str, duration: int) -> dict:
        """Renew a webhosting

        Args:
            id (str): Hosting id
            duration (int): Duration period (in months)

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "duration": duration,
        }

        return self.call("/webhosting/" + id + "/renew/", "patch", params)

    def webHostingUpdate(self, id: str, action: str, fparams: dict) -> dict:
        """Updates a webhosting

        Args:
            id (str): Hosting id
            action (str): Action name ("SetHold", "SetWebHold", "SetDBHold", "SetFTPHold", "SetMailHold", "SetPackage", "SetAutoRenew", "SetRenewReminder", "CalculateDiskUsage")
            fparams (dict): {"value":True/False} for all except SetPackage : {"offer":"SHWEB"/"SHLITE"/"SHMAIL"/"SHPREMIUM"/"SHSTART"} and CalculateDiskUsage: {}

        Throws:
            NetimAPIException

        Returns:
            dict: giving information on the status of the operation
        """
        params = {"action": action, "params": fparams}

        return self.call("/webhosting/" + id, "patch", params)

    def webHostingDelete(self, id: str, typeDelete: str) -> dict:
        """Deletes a webhosting

        Args:
            id (str): Hosting id
            typeDelete (str): Only "NOW" is allowed

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "typeDelete": typeDelete,
        }

        return self.call("/webhosting/" + id, "delete", params)

    def webHostingVhostCreate(self, id: str, fqdn: str) -> dict:
        """Creates a vhost

        Args:
            id (str): Hosting id
            fqdn (str): Fqdn of the vhost

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "fqdn": fqdn,
        }

        return self.call("/webhosting/" + id + "/vhost/", "post", params)

    def webHostingVhostUpdate(self, id: str, action: str, fparams: dict):
        """Change settings of a vhost

        Args:
            id (str): Hosting id
            action (str): Possible values :"SetStaticEngine", "SetPHPVersion",  "SetFQDN", "SetWebApplicationFirewall",
            "ResetContent", "FlushLogs", "AddAlias", "RemoveAlias", "LinkSSLCert", "UnlinkSSLCert", "EnableLetsEncrypt",
            "DisableLetsEncrypt", "SetRedirectHTTPS", "InstallWordpress", "InstallPrestashop", "SetHold"
            fparams (dict): Depends of the action

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """

        params = {
            "action": action,
            "params": fparams,
        }

        return self.call("/webhosting/" + id + "/vhost/", "patch", params)

    def webHostingVhostDelete(self, id: str, fqdn: str) -> dict:
        """Deletes a vhost

        Args:
            id (str): Hosting id
            fqdn (str): Fqdn of the vhost

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "fqdn": fqdn,
        }

        return self.call("/webhosting/" + id + "/vhost/", "delete", params)

    def webHostingDomainMailCreate(self, id: str, domain: str) -> dict:
        """Creates a mail domain

        Args:
            id (str): Hosting id
            domain (str):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "domain": domain,
        }

        return self.call("/webhosting/" + id + "/domain-mail/", "post", params)

    def webHostingDomainMailUpdate(self, id: str, action: str, fparams: dict) -> dict:
        """Change settings of mail domain based on the specified action

        Args:
            id (str): Hosting id
            action (str): Action name
            fparams (dict): Parameters of the action

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "action": action,
            "params": fparams,
        }

        return self.call("/webhosting/" + id + "/domain-mail/", "patch", params)

    def webHostingDomainMailDelete(self, id: str, domain: str) -> dict:
        """Deletes a mail domain

        Args:
            id (str): Hosting id
            domain (str):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "domain": domain,
        }

        return self.call("/webhosting/" + id + "/domain-mail/", "delete", params)

    def webHostingSSLCertCreate(
        self, id: str, sslName: str, crt: str, key: str, ca: str, csr: str = ""
    ) -> dict:
        """Creates a SSL certificate

        Args:
            id (str): Hosting id
            sslName (str): Name of the certificate
            crt (str): Content of the .crt file
            key (str): Content of the .key file
            ca (str): Content of the .ca file
            csr (str, optional): Content of the .csr file. Defaults to "".

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "sslName": sslName,
            "crt": crt,
            "key": key,
            "ca": ca,
            "csr": csr,
        }

        return self.call("/webhosting/" + id + "/ssl/", "post", params)

    def webHostingSSLCertDelete(self, id: str, sslName: str) -> dict:
        """Delete a SSL certificate

        Args:
            id (str): Hosting id
            sslName (str): Name of the certificate

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "sslName": sslName,
        }

        return self.call("/webhosting/" + id + "/ssl/", "delete", params)

    def webHostingProtectedDirCreate(
        self,
        id: str,
        fqdn: str,
        pathSecured: str,
        authname: str,
        username: str,
        password: str,
    ) -> dict:
        """Creates a htpasswd protection on a directory

        Args:
            id (str): Hosting id
            fqdn (str): FQDN of the vhost which you want to protect
            pathSecured (str): Path of the directory to protect starting from the selected vhost
            authname (str): Text shown by browsers when accessing the directory
            username (str): Login of the first user of the protected directory
            password (str): Password of the first user of the protected directory

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "fqdn": fqdn,
            "pathSecured": pathSecured,
            "authname": authname,
            "username": username,
            "password": password,
        }

        return self.call("/webhosting/" + id + "/protected-dir/", "post", params)

    def webHostingProtectedDirUpdate(self, id: str, action: str, fparams: dict) -> dict:
        """Change settings of a protected directory

        Args:
            id (str): Hosting id
            action (str): Name of the action to perform
            fparams (dict): Parameters for the action (depends of the action)

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "action": action,
            "params": fparams,
        }

        return self.call("/webhosting/" + id + "/protected-dir/", "patch", params)

    def webHostingProtectedDirDelete(
        self, id: str, fqdn: str, pathSecured: str
    ) -> dict:
        """Remove protection of a directory

        Args:
            id (str): Hosting id
            fqdn (str): Vhost's FQDN
            pathSecured (str): Path of the protected directory starting from the selected vhost

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "fqdn": fqdn,
            "path": pathSecured,
        }

        return self.call("/webhosting/" + id + "/protected-dir/", "delete", params)

    def webHostingCronTaskCreate(
        self,
        id: str,
        fqdn: str,
        path: str,
        returnMethod: str,
        returnTarget: str,
        mm: str,
        hh: str,
        jj: str,
        mmm: str,
        jjj: str,
    ) -> dict:
        """Creates a cron task

        Args:
            id (str): Hosting id
            fqdn (str): Vhost's FDQN
            path (str): Path to the script starting from the vhost's directory
            returnMethod (str): "LOG", "MAIL" or "NONE"
            returnTarget (str): When returnMethod == "MAIL" : an email address
                                When returnMethod == "LOG" : a path to a log file starting from the vhost's directory
            mm (str):
            hh (str):
            jj (str):
            mmm (str):
            jjj (str):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """

        params = {
            "fqdn": fqdn,
            "path": path,
            "returnMethod": returnMethod,
            "returnTarget": returnTarget,
            "mm": mm,
            "hh": hh,
            "jj": jj,
            "mmm": mmm,
            "jjj": jjj,
        }

        return self.call("/webhosting/" + id + "/cron-task/", "post", params)

    def webHostingCronTaskUpdate(self, id: str, action: str, fparams: dict):
        """Change settings of a cron task

        Args:
            id (str): Hosting id
            action (str): Name of the action to perform
            fparams (dict): Parameters for the performed action

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "action": action,
            "params": fparams,
        }

        return self.call("/webhosting/" + id + "/cron-task/", "patch", params)

    def webHostingCronTaskDelete(self, id: str, idCronTask: str):
        """Delete a cron task

        Args:
            id (str): Hosting id
            idCronTask (str): [description]

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "idCronTask": idCronTask,
        }

        return self.call("/webhosting/" + id + "/cron-task/", "delete", params)

    def webHostingFTPUserCreate(
        self, id: str, username: str, password: str, rootDir: str
    ) -> dict:
        """Create a FTP user

        Args:
            id (str): Hosting id
            username (str):
            password (str):
            rootDir (str): User's root directory's path starting from the hosting root

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "username": username,
            "password": password,
            "rootDir": rootDir,
        }

        return self.call("/webhosting/" + id + "/ftp-user/", "post", params)

    def webHostingFTPUserUpdate(self, id: str, action: str, fparams: dict) -> dict:
        """Update a FTP user

        Args:
            id (str): Hosting id
            action (str): Name of the action to perform
            fparams (dict): Parameters for the action (depends of the action)

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "action": action,
            "params": fparams,
        }

        return self.call("/webhosting/" + id + "/ftp-user/", "patch", params)

    def webHostingFTPUserDelete(self, id: str, username: str):
        """Delete a FTP user

        Args:
            id (str): Hosting id
            username (str):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {"username": username}

        return self.call("/webhosting/" + id + "/ftp-user/", "delete", params)

    def webHostingDBCreate(self, id: str, dbName: str, version: str = "") -> dict:
        """Create a database

        Args:
            id (str): Hosting id
            dbName (str): Name of the database (Must be preceded by the hosting id separated with a "_")
            version (str): Wanted SQL version (Optional, the newest version will be chosen if left empty)

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "dbName": dbName,
            "version": version,
        }

        return self.call("/webhosting/" + id + "/database/", "post", params)

    def webHostingDBUpdate(self, id: str, action: str, fparams: dict) -> dict:
        """Update database settings

        Args:
            id (str): Hosting id
            action (str): Name of the action to perform
            fparams (dict): Parameters for the action (depends of the action)

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "action": action,
            "fparams": fparams,
        }

        return self.call("/webhosting/" + id + "/database/", "patch", params)

    def webHostingDBDelete(self, id: str, dbName: str) -> dict:
        """Delete a database

        Args:
            id (str): Hosting id
            dbName (str): Name of the database

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "dbName": dbName,
        }

        return self.call("/webhosting/" + id + "/database/", "delete", params)

    def webHostingDBUserCreate(
        self,
        id: str,
        username: str,
        password: str,
        internalAccess: str,
        externalAccess: str,
    ) -> dict:
        """Create a database user

        Args:
            id (str): Hosting id
            username (str):
            password (str):
            internalAccess (str): "RW", "RO" or "NO"
            externalAccess (str): "RW", "RO" or "NO"

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "username": username,
            "password": password,
            "internalAccess": internalAccess,
            "externalAccess": externalAccess,
        }

        return self.call("/webhosting/" + id + "/database-user/", "post", params)

    def webHostingDBUserUpdate(self, id: str, action: str, fparams: dict) -> dict:
        """Update database user's settings

        Args:
            id (str): Hosting id
            action (str): Name of the action to perform
            fparams (dict): Parameters for the action (depends of the action)

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "action": action,
            "params": fparams,
        }

        return self.call("/webhosting/" + id + "/database-user/", "patch", params)

    def webHostingDBUserDelete(self, id: str, username: str) -> dict:
        """Delete a database user

        Args:
            id (str): Hosting id
            username (str):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "username": username,
        }

        return self.call("/webhosting/" + id + "/database-user/", "delete", params)

    def webHostingMailCreate(
        self, id: str, email: str, password: str, quota: int
    ) -> dict:
        """Create a mailbox

        Args:
            id (str): Hosting id
            email (str):
            password (str):
            quota (int): Disk space allocated to this box in MB

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """

        params = {
            "email": email,
            "password": password,
            "quota": quota,
        }

        return self.call("/webhosting/" + id + "/mailbox/", "post", params)

    def webHostingMailUpdate(self, id: str, action: str, fparams: dict) -> dict:
        """Update mailbox' settings

        Args:
            id (str): Hosting id
            action (str): Name of the action to perform
            fparams (dict): Parameters for the action (depends of the action)

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "action": action,
            "params": fparams,
        }

        return self.call("/webhosting/" + id + "/mailbox/", "patch", params)

    def webHostingMailDelete(self, id: str, email: str) -> dict:
        """Delete a mailbox

        Args:
            id (str): Hosting id
            email (str):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "email": email,
        }

        return self.call("/webhosting/" + id + "/mailbox/", "delete", params)

    def webHostingMailFwdCreate(self, id: str, source: str, destination: list) -> dict:
        """Create a mail redirection

        Args:
            id (str): Hosting id
            source (str):
            destination (list):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "source": source,
            "destination": destination,
        }

        return self.call("/webhosting/" + id + "/mail-forwarding/", "post", params)

    def webHostingMailFwdDelete(self, id: str, source: str) -> dict:
        """Delete a mail redirection

        Args:
            id (str): Hosting id
            source (str):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        params = {
            "source": source,
        }

        return self.call("/webhosting/" + id + "/mail-forwarding/", "delete", params)

    def webHostingZoneInit(self, fqdn: str, profil: int) -> dict:
        """Resets all DNS settings from a template

        Args:
            fqdn (str):
            profil (int):

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        fqdn = fqdn.lower()

        params = {
            "profil": profil,
        }

        return self.call("/webhosting/" + fqdn + "/zone/init/", "patch", params)

    def webHostingZoneInitSoa(
        self,
        fqdn: str,
        ttl: int,
        ttlUnit: str,
        refresh: int,
        refreshUnit: str,
        retry: int,
        retryUnit: str,
        expire: int,
        expireUnit: str,
        minimum: int,
        minimumUnit: str,
    ) -> dict:
        """Resets the SOA record of a domain name for a webhosting

        Args:
            fqdn (str): name of the domain
            ttl (int): time to live
            ttlUnit (str): TTL unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
            refresh (int): Refresh delay
            refreshUnit (str): Refresh unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
            retry (int): Retry delay
            retryUnit (str): Retry unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
            expire (int): Expire delay
            expireUnit (str): Expire unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'
            minimum (int): Minimum delay
            minimumUnit (str): Minimum unit. Accepted values are: 'S', 'M', 'H', 'D', 'W'

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        fqdn = fqdn.lower()

        params = {
            "ttl": ttl,
            "ttlUnit": ttlUnit,
            "refresh": refresh,
            "refreshUnit": refreshUnit,
            "retry": retry,
            "retryUnit": retryUnit,
            "expire": expire,
            "expireUnit": expireUnit,
            "minimum": minimum,
            "minimumUnit": minimumUnit,
        }

        return self.call("/webhosting/" + fqdn + "/zone/init-soa/", "patch", params)

    def webHostingZoneList(self, fqdn: str) -> list:
        """Returns all DNS records of a webhosting

        Args:
            fqdn (str): Fully qualified domain name

        Throws:
            NetimAPIException

        Returns:
            list: StructQueryZoneList
        """
        return self.call("/webhosting/" + fqdn + "/zone/", "get")

    def webHostingZoneCreate(
        self, domain: str, subdomain: str, type: str, value: str, options: dict
    ) -> dict:
        """Creates a DNS record into the webhosting domain zonefile

        Args:
            domain (str): name of the domain
            subdomain (str):
            type (str): type of DNS record. Accepted values are: 'A', 'AAAA', 'MX, 'CNAME', 'TXT', 'NS and 'SRV'
            value (str): value of the new DNS record
            options (dict): settings of the new DNS record

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation

        See:
            StructOptionsZone API http://support.netim.com/en/wiki/StructOptionsZone
        """
        fqdn = subdomain.lower() + "." + domain.lower()
        params = {
            "type": type,
            "value": value,
            "options": options,
        }

        return self.call("/webhosting/" + fqdn + "/zone/", "post", params)

    def webHostingZoneDelete(
        self, domain: str, subdomain: str, type: str, value: str
    ) -> dict:
        """Deletes a DNS record into the webhosting domain zonefile

        Args:
            domain (str): name of the domain
            subdomain (str):
            type (str): type of DNS record. Accepted values are: 'A', 'AAAA', 'MX, 'CNAME', 'TXT', 'NS and 'SRV'
            value (str): value of the new DNS record

        Throws:
            NetimAPIException

        Returns:
            dict: StructOperationResponse giving information on the status of the operation
        """
        fqdn = subdomain.lower() + "." + domain.lower()
        params = {
            "type": type,
            "value": value,
        }

        return self.call("/webhosting/" + fqdn + "/zone/", "delete", params)
