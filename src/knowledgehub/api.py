# (C) 2021, Erasmus University Medical Center

import json
import requests
import urllib3
import sys

#
# this is the API for all services provided by the KnowledgeHubAPI
#
from . import semanticservice, similarityservice, chemistryservice, primitiveadapter, services, constants


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


    username = None
    password = None
    ss = None
    medline = None
    faers = None
    clinicaltrials = None
    dailymed = None
    etoxsys = None
    simsrv = None
    chemserv = None
    services = None
    service = None
    servers = {
                # 'DEV': Service('3db5a6d7-4694-48a4-8a2e-e9c30d78f9ab', 'https://dev.toxhub.etransafe.eu', 'https://login.dev.toxhub.etransafe.eu'),
                # 'TEST': Service('39c644b3-1f23-4d94-a71f-e0fb43ebd760', 'https://test.toxhub.etransafe.eu','https://login.test.toxhub.etransafe.eu')
                'DEV': Service(None, 'https://dev.toxhub.etransafe.eu', 'https://login.dev.toxhub.etransafe.eu'),
                'TEST': Service(None, 'https://test.toxhub.etransafe.eu', 'https://login.test.toxhub.etransafe.eu')
    }

    def __init__(self, server='TEST', client_secret=None):
        urllib3.disable_warnings()
        self.set_server(server)
        self.set_client_secret(client_secret)

    def set_server(self, server):
        self.server = server

    def get_server(self, name=None):
        return self.servers[name] if name is not None else self.servers[self.server]

    def get_keycloak(self):
        return self.servers[self.server].get_keycloak()

    def get_client_secret(self):
        return self.servers[self.server].get_client_secret()

    def set_client_secret(self, client_secret):
        return self.servers[self.server].set_client_secret(client_secret=client_secret)

    def get_token(self):
        return self.servers[self.server].get_token()

    def set_token(self, token):
        self.servers[self.server].set_token(token)

    def get_base(self):
        return self.servers[self.server].get_base()

    def login(self, username, password):
        self.username = username
        self.password = password
        data = {'grant_type': 'password', 'username': username, 'password': password, 'client_id': 'knowledge-hub', 'client_secret': self.get_client_secret()}
        r = requests.post(f'{self.get_keycloak()}/auth/realms/KH/protocol/openid-connect/token', verify=False, data=data)
        if r.status_code == 200:
            self.set_token(json.loads(r.text)["access_token"])
        else:
            print(r.status_code)

        return r.status_code == 200

    def reconnect(self):
        status = self.login(self.username, self.password)
        if not status:
            print('failed to reconnect')
            sys.exit()

    def SemanticService(self):
        if self.ss is None:
            self.ss = semanticservice.SemanticService(self, self.get_base())
        return self.ss

    def SimilarityService(self):
        if self.simsrv is None:
            self.simsrv = similarityservice.SimilarityService(self, self.get_base())
        return self.simsrv

    def ChemistryService(self):
        if self.chemserv is None:
            self.chemserv = chemistryservice.ChemistryService(self, self.get_base())
        return self.chemserv

    def Offtarget(self):
        if self.offtarget is None:
            self.offtarget = primitiveadapter.PrimitiveAdapter(self, self.get_base() + "/offtarget.kh.svc/primitive-adapter/v1/", mode=constants.INITIALIZE_1)
        return self.offtarget

    def Medline(self):
        if self.medline is None:
            self.medline = primitiveadapter.PrimitiveAdapter(self, self.get_base() + "/medlinepa.kh.svc/primitive-adapter/v1/", mode=constants.INITIALIZE_1)
        return self.medline

    def Faers(self):
        if self.faers is None:
            self.faers = primitiveadapter.PrimitiveAdapter(self, self.get_base() + "/faerspa.kh.svc/primitive-adapter/v1/", mode=constants.USE_SEVERITY)
        return self.faers

    def ClinicalTrials(self):
        if self.clinicaltrials is None:
            self.clinicaltrials = primitiveadapter.PrimitiveAdapter(self, self.get_base() + "/clinicaltrialspa.kh.svc/primitive-adapter/v1/", mode=constants.USE_SEVERITY)
        return self.clinicaltrials

    def DailyMed(self):
        if self.dailymed is None:
            self.dailymed = primitiveadapter.PrimitiveAdapter(self, self.get_base() + "/dailymedpa.kh.svc/primitive-adapter/v1/", mode=constants.INITIALIZE_1)
        return self.dailymed

    def eToxSys(self):
        if self.etoxsys is None:
            self.etoxsys = primitiveadapter.PrimitiveAdapter(self, self.get_base() + "/etoxsyspa.kh.svc/preclinical-platform/api/etoxsys-pa/v1/", mode=constants.INITIALIZE_1)
        return self.etoxsys

    def Services(self):
        if self.services is None:
            self.services = services.Services(self, self.get_base())
        return self.services
