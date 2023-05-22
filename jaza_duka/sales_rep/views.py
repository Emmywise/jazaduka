from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from jaza_duka.payments.models import Outlet

from .models import SalesRep


class GetDukaSalesRepNumber(APIView):
    def get(self, request):

        phonenumber = request.query_params.get("phonenumber")
        salesReps = SalesRep.objects.filter(phone_number=phonenumber).first()
        duka = Outlet.objects.filter(
            Q(phone_number=phonenumber) & Q(status="AP")
        ).first()
        if salesReps:
            return Response(
                {"salesrep": salesReps.id, "is_duka": False}, status=status.HTTP_200_OK
            )
        if duka:
            return Response(
                {"duka_id": duka.id, "is_duka": True}, status=status.HTTP_200_OK
            )
        return Response(
            {"Message": "Phone Number does not exist"}, status=status.HTTP_404_NOT_FOUND
        )
