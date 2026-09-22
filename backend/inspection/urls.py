from django.urls import path

from inspection import views

urlpatterns = [
    path("health/", views.health, name="health"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", views.list_view, name="list"),
    path("reconcile/", views.reconcile_view, name="reconcile"),
    path("inspections/new/", views.create_view, name="create"),
    path("inspections/<int:pk>/", views.detail_view, name="detail"),
    path("inspections/<int:pk>/verdict/", views.verdict_edit_view, name="verdict_edit"),
    path("inspections/<int:pk>/rewrite/", views.reconcile_rewrite_view, name="reconcile_rewrite"),
]
