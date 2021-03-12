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


class Service():
    service = None

    def __init__(self, service):
        self.service = service

    def get_service_type(self):
        return self.service['serviceType'] if self.service is not None and 'serviceType' in self.service else None

    def get_title(self):
        return self.service['title'] if self.service is not None else None

    def get_address(self):
        return self.service['address'] if self.service is not None else None

class Services():
    services = []
    endpoint = None

    def __init__(self, token, endpoint):
        self.token = token
        self.endpoint = endpoint
        r = requests.get(self.endpoint + '/service', verify=False, headers={'Authorization': f'Bearer {self.token}'})
        if r.status_code == 200:
            service_list = json.loads(r.text)
            for service_desc in service_list:
                self.services.append(Service(service_desc))
        else:
            print(f'Cannot retrieve service information from {self.endpoint}: {r.status_code}')

    def get(self, serviceType = None):
        result = []
        for service in self.services:
            if serviceType is None or service.get_service_type() == serviceType:
                result.append(service)
        return result

