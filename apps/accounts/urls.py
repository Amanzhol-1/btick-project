# Django modules
from django.urls import path, include

# Django Rest Framework modules
from rest_framework.routers import DefaultRouter

# Third-party modules
from rest_framework_simplejwt.views import TokenRefreshView

# Project modules
from apps.accounts.views import AccountViewSet


router: DefaultRouter = DefaultRouter(trailing_slash=False)

router.register(
    prefix="",
    viewset=AccountViewSet,
    basename="account",
)

app_name: str = "accounts"

urlpatterns: list = [
    path("", include(router.urls)),
    path("token/refresh", TokenRefreshView.as_view(), name="token_refresh"),
]
