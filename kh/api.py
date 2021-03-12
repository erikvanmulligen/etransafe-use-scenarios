import json
import requests
import urllib3
from kh import semanticservice
from kh import similarityservice
from kh import primitiveadapter

#
# this is the API for all services provided by the KnowledgeHubAPI
#

class Service:
    client_secret = None
    base = None
    keycloak = None
    token = None

    def __init__(self, client_secret, base, keycloak):
        self.set_client_secret(client_secret)
        self.set_keycloak(keycloak)
        self.set_base(base)

    def set_token(self, token):
        self.token = token

    def get_token(self):
        return self.token

    def set_client_secret(self, client_secret):
        self.client_secret = client_secret

    def get_client_secret(self):
        return self.client_secret

    def set_keycloak(self, keycloak):
        self.keycloak = keycloak

    def get_keycloak(self):
        return self.keycloak

    def set_base(self, base):
        self.base = base

    def get_base(self):
        return self.base


class KnowledgeHubAPI:
    ss = None
    medline = None
    faers = None
    clinicaltrials = None
    etoxsys = None
    simsrv = None
    service = None
    services = {
                'DEV': Service('99402d5f-897e-4e27-881e-85cb04f75601', 'https://a05f2bb1dd55e4b78b61a78a780a5e5c-96677817.eu-west-1.elb.amazonaws.com', 'https://k8s-kh-keycloak-430ca1efd8-484945488.eu-west-1.elb.amazonaws.com'),
                'TEST': Service('39c644b3-1f23-4d94-a71f-e0fb43ebd760', 'https://aead2da1a152644f797ca358c0975f8e-1350926270.eu-west-1.elb.amazonaws.com', 'https://k8s-kh-keycloak-430ca1efd8-484945488.eu-west-1.elb.amazonaws.com')
    }

    def __init__(self):
        urllib3.disable_warnings()
        self.set_service('TEST')

    def set_service(self, service):
        self.service = service

    def get_service(self, name=None):
        return self.services[name] if name is not None else self.services[self.service]

    def get_keycloak(self):
        return self.services[self.service].get_keycloak()

    def get_client_secret(self):
        return self.services[self.service].get_client_secret()

    def get_token(self):
        return self.services[self.service].get_token()

    def set_token(self, token):
        self.services[self.service].set_token(token)

    def get_base(self):
        return self.services[self.service].get_base()

    def login(self, username, password):
        data = {'grant_type': 'password', 'username': username, 'password': password, 'client_id': 'knowledge-hub', 'client_secret': self.get_client_secret()}
        r = requests.post(f'{self.get_keycloak()}/auth/realms/KH/protocol/openid-connect/token', verify=False, data=data)

        if r.status_code == 200:
            self.set_token(json.loads(r.text)["access_token"])
        else:
            print(r.status_code)

        return r.status_code == 200

    def SemanticService(self):
        if self.ss is None:
            self.ss = semanticservice.SemanticService(self.get_token(), self.get_base())
        return self.ss

    def SimilarityService(self):
        if self.simsrv is None:
            self.simsrv = similarityservice.SimilarityService(self.get_token(), self.get_base())
        return self.simsrv

    def Medline(self):
        if self.medline is None:
            self.medline = primitiveadapter.PrimitiveAdapter(self.get_token(), self.get_base() + "/medlinepa.kh.svc/primitive-adapter/v1/")
        return self.medline

    def Faers(self):
        if self.faers is None:
            self.faers = primitiveadapter.PrimitiveAdapter(self.get_token(), self.get_base() + "/faerspa.kh.svc/primitive-adapter/v1/")

        return self.faers

    def ClinicalTrials(self):
        if self.clinicaltrials is None:
            self.clinicaltrials = primitiveadapter.PrimitiveAdapter(self.get_token(), self.get_base() + "/clinicaltrialspa.kh.svc/primitive-adapter/v1/")
        return self.clinicaltrials

    def eToxSys(self):
        if self.etoxsys is None:
            self.etoxsys = primitiveadapter.PrimitiveAdapter(self.get_token(), self.get_base() + "/etoxsyspa.kh.svc/preclinical-platform/api/etoxsys-pa/v1/")
        return self.etoxsys