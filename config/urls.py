from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path, re_path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from rest_framework.authtoken.views import obtain_auth_token

from jaza_duka.products import views as products_views
from jaza_duka.sales_rep import views as duka_number

schema_view = get_schema_view(
    openapi.Info(
        title="Jaza Duka",
        default_version="v1",
        description="Jaza Duka Program",
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)


def homePageView(request):
    return HttpResponse("Server Runninggg!")


urlpatterns = [
    path("", homePageView, name="home"),
    path(
        "about/", TemplateView.as_view(template_name="pages/about.html"), name="about"
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    # path("users/", include("jaza_duka.users.urls", namespace="users")),
    # Your stuff: custom urls includes go here
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# API URLS
urlpatterns += [
    # API base url
    path("api/", include("config.api_router")),
    path("paymentapi/", include("jaza_duka.payments.api_urls")),
    path("payments/", include("jaza_duka.payments.urls")),
    # DRF auth token
    path("auth-token/", obtain_auth_token),
    path("product/list", products_views.ProductList.as_view(), name="product-list"),
    path(
        "salerep",
        duka_number.GetDukaSalesRepNumber.as_view(),
        name="duka-sales-rep-number",
    ),
]

if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
        re_path(
            "^swagger(?P<format>.json|.yaml)$",
            schema_view.without_ui(cache_timeout=0),
            name="schema-json",
        ),
        path(
            "swagger/",
            schema_view.with_ui("swagger", cache_timeout=0),
            name="schema-swagger-ui",
        ),
        path(
            "redoc/", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"
        ),
    ]
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns


admin.site.site_header = "Jaza Duka Admin"
admin.site.site_title = "Jaza Duka Portal"
