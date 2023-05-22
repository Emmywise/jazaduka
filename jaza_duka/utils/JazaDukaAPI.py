import requests
from django.conf import settings


class DukAPIConnector:
    def __init__(self) -> None:
        self.base_url = settings.DUKA_URL
        self.headers = settings.REQ_HEADERS

    def confirm_action(self, batch_id):
        """Confirm a GET request to remains same for pre-auth, charge, refund"""
        url = self.base_url + "/" + batch_id
        if batch_id:
            try:
                resp = requests.get(
                    url,
                    headers=self.headers,
                    auth=(settings.DUKA_HTTP_AUTH_USER, settings.DUKA_HTTP_AUTH_PASS),
                    timeout=15,
                )
                if resp.ok:
                    return resp.json()
            except requests.exceptions.RequestException:
                pass
            return None
