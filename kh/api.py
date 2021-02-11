import json
import requests
import urllib3
from kh import semanticservice
from kh import similarityservice
from kh import primitiveadapter

#
# this is the API for all services provided by the KnowledgeHubAPI
#


class KnowledgeHubAPI:
    token = None
    ss = None
    medline = None
    faers = None
    clinicaltrials = None
    etoxsys = None
    simsrv = None
    client_secret = "99402d5f-897e-4e27-881e-85cb04f75601"
    #base = 'https://dev.kh.etransafe.eu'
    base = 'https://a05f2bb1dd55e4b78b61a78a780a5e5c-96677817.eu-west-1.elb.amazonaws.com'

    def __init__(self):
        urllib3.disable_warnings()

    def login(self, username, password):
        r = requests.post("https://login.etransafe.eu/auth/realms/KH/protocol/openid-connect/token",
                          verify=False,
                          data={
                              "grant_type": "password",
                              "username": username,
                              "password": password,
                              "client_id": "knowledge-hub",
                              "client_secret": self.client_secret
                          }
                          )

        if r.status_code == 200:
            data = json.loads(r.text)
            self.token = data["access_token"]
            print(f'token:{self.token}')
        else:
            print(r.status_code)

        return r.status_code == 200

    def SemanticService(self):
        if self.ss is None:
            self.ss = semanticservice.SemanticService(self.token, self.base)
        return self.ss

    def SimilarityService(self):
        if self.simsrv is None:
            self.simsrv = similarityservice.SimilarityService(self.token, self.base)
        return self.simsrv

    def Medline(self):
        if self.medline is None:
            self.medline = primitiveadapter.PrimitiveAdapter(self.token,
                                                             self.base + "/medlinepa.kh.svc/primitive-adapter/v1/query")
        return self.medline

    def Faers(self):
        if self.faers is None:
            self.faers = primitiveadapter.PrimitiveAdapter(self.token,
                                                           self.base + "/faerspa.kh.svc/primitive-adapter/v1/query")

        return self.faers

    def ClinicalTrials(self):
        if self.clinicaltrials is None:
            self.clinicaltrials = primitiveadapter.PrimitiveAdapter(self.token,
                                                                    self.base + "/clinicaltrialspa.kh.svc/primitive-adapter/v1/query")
        return self.clinicaltrials

    def eToxSys(self):
        if self.etoxsys is None:
            self.etoxsys = primitiveadapter.PrimitiveAdapter(self.token,
                                                             self.base + "/etoxsyspa.kh.svc/preclinical-platform/api/etoxsys-pa/v1/query")
        return self.etoxsys
