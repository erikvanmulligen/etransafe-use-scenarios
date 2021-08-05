#
# this module the interface to the kubernetes service registry. This allows auto detect of new (data) services
#
# Copyright (C) 2021, dept of Medical Informatics, Erasmus University Medical Center, Rotterdam, The Netherlands
# Erik M. van Mulligen, e.vanmulligen@erasmusmc.nl
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Erasmus University Medical Center, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import json
import requests
import urllib3


class Services():
    services = None
    base = None
    api = None

    def __init__(self, api, base):
        urllib3.disable_warnings()
        self.api = api
        self.base = base

    def __get_token(self):
        return self.api.get_token()

    def get(self, serviceType=None):
        if self.services is None:
            self.services = []
            r = requests.get(self.base + "/registry.kh.svc/api/v1/service", verify=False, headers={"Authorization": f"Bearer {self.__get_token()}"})
            if r.status_code == 200:
                service_list = json.loads(r.text)
                for service_desc in service_list:
                    self.services.append(service_desc)
            else:
                print(f'Cannot retrieve service information from {self.base}: {r.status_code}')

        result = []
        for service in self.services:
            if serviceType is None or service['service_type'] == serviceType:
                result.append(service)
        return result

