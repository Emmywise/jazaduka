import json
import logging
import time

import pandas as pd
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.core.mail import send_mail
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from woocommerce import API

from config import celery_app
from jaza_duka.duka_zones.models import Zone
from jaza_duka.sales_rep.models import SalesRep
from jaza_duka.utils.JazaDukaAPI import DukAPIConnector

from .models import Outlet, Payment, PaymentLog, Refund, RefundLog

User = get_user_model()

logger = logging.getLogger(__name__)


@celery_app.task
def sync_payment_records(payment_id: int, action: str):
    logger.info(f"start sync_payment_records for {payment_id} {action}")
    payment_obj = Payment.objects.get(id=payment_id)
    log_obj = PaymentLog.objects.get(payment_id=payment_obj)
    duka_api = DukAPIConnector()
    if action == "pre-auth":
        resp = duka_api.confirm_action(log_obj.pre_auth_batch_id)
        logger.info(f"sync_payment_records response from Duka API: {resp}")
        try:
            payment_obj.pre_auth_confirmation_status = resp["content"]["orders"][0][
                "status"
            ]
        except KeyError:
            payment_obj.pre_auth_confirmation_status = "FAILED"
        log_obj.pre_auth_get_response = resp

    elif action == "charge":
        resp = duka_api.confirm_action(log_obj.charge_request_batch_id)
        try:
            payment_obj.payment_status = resp["content"]["orders"][0]["status"]
        except KeyError:
            payment_obj.payment_status = "FAILED"
        log_obj.charge_request_get_response = resp

    payment_obj.save()
    log_obj.save()
    logger.info(f"end sync_payment_records for {payment_id} {action}")


@celery_app.task()
def post_request(obj_id, action, auto_charge=False, auto_verify=False):
    payment_obj = Payment.objects.get(id=int(obj_id))
    logger.info(f"start-post-request {payment_obj.id} {action}")

    if action == "AR":
        log_obj = PaymentLog(payment_id=payment_obj)
        amount = payment_obj.amount_auth
        logger.info(f"order-id{payment_obj.order_id}")

    elif action == "CR":
        if payment_obj.pre_auth_confirmation_status != "APPROVED":
            return False
        amount = payment_obj.amount_requested
        log_obj = PaymentLog.objects.filter(payment_id=payment_obj).first()
        logger.info(f"payment-id {payment_obj.id}")

    elif action == "RR":
        refund_obj = Refund.objects.filter(payment_id__pk=obj_id).first()
        amount = refund_obj.refunded_amount
        log_obj = RefundLog(payment_id=payment_obj)
        logger.info(f"payment-id {payment_obj.id}")

    data = {
        "action": action,
        "orders": [
            {
                "outletCode": payment_obj.outlet.outlet_code,
                "distributorId": settings.DISTRIBUTOR_ID,
                "orderId": payment_obj.order_id,
                "amount": amount,
                "currency": payment_obj.currency,
            }
        ],
    }
    logger.info(f"post_request request: {settings.DUKA_URL} data: {data}")
    resp = requests.post(
        settings.DUKA_URL,
        data=json.dumps(data, cls=DjangoJSONEncoder),
        headers=settings.REQ_HEADERS,
        auth=(settings.DUKA_HTTP_AUTH_USER, settings.DUKA_HTTP_AUTH_PASS),
    )
    if resp.status_code == 202 or resp.status_code == 422:
        if action == "AR":
            payment_obj.pre_auth_status = resp.json()["message"]
            log_obj.pre_auth_batch_id = resp.json()["content"]["batchId"]
            log_obj.pre_auth_response = resp.json()
            logger.info(f"post-pre-auth-response {resp.json()}")

        elif action == "CR":
            log_obj.charge_request_batch_id = resp.json()["content"]["batchId"]
            log_obj.charge_request_response = resp.json()
            payment_obj.payment_request_status = resp.json()["message"]
            logger.info(f"post-charge-request-response {resp.json()}")

        elif action == "RR":
            refund_obj.refund_auth_status = resp.json()["message"]
            refund_obj.save()
            log_obj.post_request_response = resp.json()
            log_obj.refund_batch_id = resp.json()["content"]["batchId"]
            logger.info(f"post-refund-request-response {resp.json()}")

    else:
        logger.error("failed-tasks- post-request -->", resp.content)
        log_obj.post_failure_log = resp.json()
        return [payment_obj.id, action, None]

    payment_obj.save()
    log_obj.save()
    logger.info(f"end-post-request {payment_obj.id} {action}")
    return [payment_obj.id, action]


@celery_app.task()
def confirm_get_request(attr):
    logger.info(f"start-confirm-get-request {attr}")
    if type(attr) == bool:
        return False

    action = attr[1]
    payment_obj = Payment.objects.get(id=int(attr[0]))

    if action == "RR":
        payment_log_obj = RefundLog.objects.filter(payment_id=payment_obj).first()

    elif action == "AR":
        payment_log_obj = PaymentLog.objects.filter(payment_id=payment_obj).first()

    elif action == "CR":
        payment_log_obj = PaymentLog.objects.filter(payment_id=payment_obj).first()

    if attr[-1] is not None:
        if action == "RR":
            batch_id = payment_log_obj.refund_batch_id
        elif action == "AR":
            batch_id = payment_log_obj.pre_auth_batch_id
        elif action == "CR":
            batch_id = payment_log_obj.charge_request_batch_id

        BATCH_URL = settings.DUKA_URL + "/" + batch_id
        logger.info(f"confirm-get-request {BATCH_URL}")
        resp = requests.get(
            BATCH_URL,
            headers=settings.REQ_HEADERS,
            auth=(settings.DUKA_HTTP_AUTH_USER, settings.DUKA_HTTP_AUTH_PASS),
        )
        # If the batch is still in progress, wait for it to complete
        if resp.status_code == 202:
            while resp.status_code == 202:
                time.sleep(5)
                logger.info("waiting-loop waiting for 5 seconds")
                resp = requests.get(
                    BATCH_URL,
                    headers=settings.REQ_HEADERS,
                    auth=(settings.DUKA_HTTP_AUTH_USER, settings.DUKA_HTTP_AUTH_PASS),
                )
                if resp.status_code == 202:
                    continue
                else:
                    logger.info("end waiting-loop confirm-get-request")
                    break

        if resp.status_code == 200:
            logger.info("confirm-get-request response.ok")
            if action == "AR":
                try:
                    payment_obj.pre_auth_confirmation_status = resp.json()["content"][
                        "orders"
                    ][0]["status"]
                    payment_log_obj.pre_auth_get_response = resp.json()
                    logger.info(
                        f"confirm-get-request complete pre-auth-response {resp.json()}"
                    )
                except KeyError as e:
                    payment_log_obj.pre_auth_get_response = f"KeyError for {str(e)}"
                    payment_obj.pre_auth_confirmation_status = "FAILED"
                    logger.error(f"confirm-get-request KeyError {str(e)}")

                    # send notification sms when failed
                    order_id = payment_obj.order_id
                    headers = {
                        "Content-Type": "application/json",
                        "Authorization": f"Token {settings.USSD_API_KEY}",
                    }
                    data = {"order_id": order_id}
                    requests.post(
                        f"{settings.USSD_URL}failed/pre-auth/sms/",
                        headers=headers,
                        json=data,
                    )

            elif action == "CR":
                payment_obj.payment_request_date = timezone.now()
                payment_obj.payment_status = resp.json()["content"]["orders"][0][
                    "status"
                ]
                payment_log_obj.charge_request_get_response = resp.json()
                logger.info(
                    f"confirm-get-request complete charge-request-response {resp.json()}"
                )

            elif action == "RR":
                refund_obj = Refund.objects.filter(payment_id=payment_obj).first()
                refund_obj.refund_confirm_status = resp.json()["content"]["orders"][0][
                    "status"
                ]
                payment_obj.refunded = True
                refund_obj.save()
                payment_log_obj.get_request_response = resp.json()
                logger.info(
                    f"confirm-get-request complete refund-request-response {resp.json()}"
                )
        else:
            logger.error(f"confirm-get-request response status {resp.status_code}")
            logger.error(f"failed confirm-get-request --> {resp.json()}")
            payment_log_obj.get_failure_log = resp.json()
            if action == "AR":
                payment_obj.pre_auth_confirmation_status = "FAILED"
            elif action == "CR":
                payment_obj.payment_status = "FAILED"
            elif action == "RR":
                refund_obj = Refund.objects.filter(payment_id=payment_obj).first()
                refund_obj.refund_confirm_status = "FAILED"
                refund_obj.save()
    else:
        if action == "AR":
            payment_obj.pre_auth_confirmation_status = "FAILED"
        elif action == "CR":
            payment_obj.payment_status = "FAILED"

    payment_obj.pre_auth_verified = True
    payment_obj.save()
    logger.info(f"end-confirm-get-request {payment_obj.id} {action}")
    payment_log_obj.save()


@celery_app.task()
def update_wc_status(obj_id):
    logger.info("start-update-wc-status")
    payment_obj = Payment.objects.get(pk=obj_id)
    order_id = payment_obj.order_id
    outlet_obj = Outlet.objects.get(outlet_code=payment_obj.outlet)
    outlet_names = outlet_obj.outlet_name
    salesrep_obj = SalesRep.objects.get(name=outlet_obj.sales_rep)
    zone_obj = Zone.objects.get(name=salesrep_obj.jaza_duka_zone)
    zone_name = zone_obj.name
    logger.info(
        f"wc-status-update {payment_obj} {order_id} {outlet_names} {salesrep_obj} {zone_name}"
    )
    wcapi = API(
        url=settings.KE_WOO_COMMERCE_URL,
        consumer_key=settings.KE_CONSUMER_KEY,
        consumer_secret=settings.KE_SECURITY_KEY,
        wp_api=True,
        query_string_auth=True,
        verify_ssl=True,
        version="wc/v3",
        timeout=10,
    )
    if payment_obj.payment_status == "APPROVED":
        data = {
            "status": "verified",
            "set_paid": True,
            "payment_method": "jazaduka",
            "billing": {
                "first_name": outlet_names,
                "address_1": zone_name,
            },
            "shipping": {
                "last_name": outlet_names,
                "address_1": zone_name,
                "city": "Nairobi",
            },
            "meta_data": [
                {"key": "_payment_method", "value": "Jazaduka"},
                {"key": "_payment_method_title", "value": "Jazaduka"},
                {"key": "_jazaduka_transaction_id", "value": payment_obj.id},
            ],
        }
        link = f"orders/{order_id}"
        try:
            # WC has a bug, the order isn't set to paid even though that's what we asked for
            # there's a secondary endpoint that addresses this [but can't set meta_data...]
            resp = wcapi.put(link, data)
            logger.info(f"order-updated, {resp.json()}")
            resp = wcapi.put(f"custom-order-update/{order_id}", data)
            logger.info(f"order-payment-updated, {resp.json()}")
        except requests.RequestException as e:
            logger.error(f"order-update-failed, {str(e)}")
    elif payment_obj.pre_auth_confirmation_status == "FAILED":
        data = {
            "status": "canceled",
            "meta_data": [
                {"key": "_payment_method", "value": "Jazaduka"},
                {"key": "_payment_method_title", "value": "Jazaduka"},
                {"key": "_jazaduka_transaction_id", "value": payment_obj.id},
            ],
        }
        link = f"orders/{order_id}"
        wcapi.put(link, data)
    else:
        data = {
            "status": "canceled",
            "meta_data": [
                {"key": "_payment_method", "value": "Jazaduka"},
                {"key": "_payment_method_title", "value": "Jazaduka"},
                {"key": "_jazaduka_transaction_id", "value": payment_obj.id},
            ],
        }
        link = f"orders/{order_id}"
        wcapi.put(link, data)


@celery_app.task()
def upload_outlets(file_name, uploader_id):
    uploaded_file = default_storage.open(file_name, "rb")
    logger.info(f"start-upload-outlets {file_name}")
    df = pd.read_excel(uploaded_file, header=1)
    duplicate_list = []
    uploaded_dukas = []
    exceptions = []
    user = User.objects.get(id=uploader_id)

    for row in df.itertuples():
        outlet_name = row[1]
        outlet_code = row[2]
        route_name = row[4]
        align_code = row[5]

        try:
            Outlet.objects.get(outlet_code=outlet_code)
            duplicate_list.append(outlet_name)

        except Outlet.DoesNotExist:
            try:
                # Creating objects in loop instead of bulk to catch the failed outlets
                Outlet.objects.create(
                    outlet_name=outlet_name,
                    outlet_code=outlet_code,
                    route_name=route_name,
                    align_code=align_code,
                    created_by=user,
                )
                uploaded_dukas.append(outlet_name)
            except Exception as e:
                logger.error("failed-upload-outlets -->", e)
                exceptions.append(outlet_name)

    logger.info("upload-outlets  sending mail to-->", user.email)
    send_mail(
        # Subject
        "Duka uploading finished",
        # Email body
        """
            hi,

            Duka-stores/Outlet upload completed -

            Here are the logs,

            Duplicate dukas - {}

            Successfully uploaded - {}

            Exceptions - {}

            Thanks

        """.format(
            duplicate_list, uploaded_dukas, exceptions
        ),
        "jazaduka@kasha.co",
        [user.email],
        fail_silently=False,
    )
    logger.info(f"end-upload-outlets {file_name}")
