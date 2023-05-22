from django.contrib import admin

from .models import ProductsList


@admin.register(ProductsList)
class ProductsAdmin(admin.ModelAdmin):
    list_display = ["id", "product_id", "description", "image_url", "price", "currency"]
    search_fields = ["product_id"]
    list_per_page = 20
