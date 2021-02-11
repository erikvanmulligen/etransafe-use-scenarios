import json
import requests
import urllib3

#urllib3.disable_warnings()


def login(username, password):
    r = requests.post("https://login.etransafe.eu/auth/realms/KH/protocol/openid-connect/token",
                      verify=False,
                      # CA of SSL certificate of login.etransafe.eu server is NOT recognized for whatever reason
                      data={
                          "grant_type": "password",
                          "username": username,
                          "password": password,
                          "client_id": "knowledge-hub",
                          "client_secret": "99402d5f-897e-4e27-881e-85cb04f75601"}
                      )

    print("Login result:", r.status_code)

    if r.status_code == 200:
        # get the authentication token
        data = json.loads(r.text)
        token = data["access_token"]
        # set it as header "Authorization: Bearer ..."
        # and use it for all consequent requests to KH
        print(token)

        r = requests.get("https://dev.kh.etransafe.eu/khrfrontend.kh.svc/",
                         verify=False,
                         # CA of SSL certificate of login.etransafe.eu server is NOT recognized for whatever reason
                         headers={
                             "Authorization": f"Bearer {token}"
                         }
                         )
        print("Access result:", r.status_code)

        return token

    else:
        print(f"Cannot login: {r.status_code}")
        print(r.text)

        return None


if __name__ == "__main__":
    login('e.vanmulligen@erasmusmc.nl', 'Crosby99')