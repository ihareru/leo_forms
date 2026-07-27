from django.contrib.auth.views import LogoutView
from django.urls import path

from .views import PortalLoginView, dashboard


app_name = "accounts"


urlpatterns = [
    path(
        "login/",
        PortalLoginView.as_view(),
        name="login",
    ),
    path(
        "logout/",
        LogoutView.as_view(),
        name="logout",
    ),
    path(
        "",
        dashboard,
        name="dashboard",
    ),
]