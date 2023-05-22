import json


class MockResponse:
    """
    MockResponse Class
    """

    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code
        self.ok = self.status_code == 200

    def __str__(self):
        return json.dumps(self.json_data)

    def json(self):
        return self.json_data

    def content(self):
        return self.json_data


pre_auth_post_response = {
    "status": 202,
    "error": "",
    "message": "Batch Received",
    "content": {
        "properties": {},
        "batchId": "KASHA_45ece6cd3857edc1b104770e7139133814ae1999_AUTH",
        "timeProcessing": 0,
        "progress": 0.0,
    },
}

pre_auth_get_response = {
    "status": 200,
    "error": "",
    "message": "Ready",
    "content": {
        "batchId": "KASHA_45ece6cd3857edc1b104770e7139133814ae1999_AUTH",
        "orders": [
            {
                "properties": None,
                "outletCode": "TEST-OUTLET-1",
                "distributorId": "K001",
                "orderId": "KE822234239",
                "transactionId": None,
                "status": "APPROVED",
                "currency": "KES",
                "amount": "100.00",
                "reason": None,
            }
        ],
        "timeProcessing": 8991,
        "progress": 100.0,
    },
}


charge_post_response = {
    "status": 202,
    "error": "",
    "message": "Batch Received",
    "content": {
        "properties": {},
        "batchId": "KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE",
        "timeProcessing": 0,
        "progress": 0.0,
    },
}


charge_get_response = {
    "error": "",
    "status": 200,
    "content": {
        "orders": [
            {
                "amount": "100.00",
                "status": "APPROVED",
                "orderId": "KE123",
                "currency": "KES",
                "outletCode": "OUTLET1",
                "distributorId": "K001",
            }
        ],
        "batchId": "KASHA_d8cb515ea19903daa9b146d684df639f5961ea8f_CAPTURE",
        "progress": 100.0,
        "timeProcessing": 3184,
    },
    "message": "Ready",
}

refund_post_response = {
    "status": 202,
    "error": "",
    "message": "Batch Received",
    "content": {
        "properties": {},
        "batchId": "KASHA_0359ab95810bab36963a5c7c44bb33ff62a30b0a_REFUND",
        "timeProcessing": 0,
        "progress": 0.0,
    },
}

refund_get_response = {
    "status": 200,
    "error": "",
    "message": "Ready",
    "content": {
        "batchId": "KASHA_0359ab95810bab36963a5c7c44bb33ff62a30b0a_REFUND",
        "orders": [
            {
                "properties": None,
                "outletCode": "OUTLET2",
                "distributorId": "K001",
                "orderId": "KN122",
                "transactionId": None,
                "status": "APPROVED",
                "currency": "KES",
                "amount": "100.00",
                "reason": None,
            }
        ],
        "timeProcessing": 4950,
        "progress": 100.0,
    },
}
