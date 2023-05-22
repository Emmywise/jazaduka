from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ProductsList
from .serializers import ProductListSerializer


class ProductList(APIView):
    def post(self, request):
        serializer = ProductListSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request, pk=None):
        queryset = ProductsList.objects.all()
        serializer = ProductListSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
