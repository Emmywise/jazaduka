import logging

from jaza_duka.payments.models import PaymentLog
from jaza_duka.utils.JazaDukaAPI import DukAPIConnector

logger = logging.getLogger(__name__)


def has_identical_record(payment_obj, action: str):
    logger.info(f"start has_identical_record for {payment_obj.id} {action}")
    log_obj = PaymentLog.objects.get(payment_id=payment_obj)
    api = DukAPIConnector()
    if action == "pre-auth":
        if log_obj.pre_auth_batch_id is None:
            # We can not confirm pre-auth without the batch id
            pass
        resp = api.confirm_action(log_obj.pre_auth_batch_id)
        if (
            payment_obj.pre_auth_confirmation_status
            != resp["content"]["orders"][0]["status"]
        ):
            return False

    elif action == "charge":
        if log_obj.charge_request_batch_id is None:
            # We can not confirm charge without the batch id
            pass
        try:
            resp = api.confirm_action(log_obj.charge_request_batch_id)
            if payment_obj.payment_status != resp["content"]["orders"][0]["status"]:
                return False
        except Exception as e:
            logger.error(f"batch-id-empty{str(e)}")
    logger.info("end has_identical_record")
    return True
