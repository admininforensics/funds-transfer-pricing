from django.urls import path

from . import views


urlpatterns = [
    path("", views.home_redirect, name="home"),
    path("runs/", views.run_dashboard, name="run_dashboard"),
    path("runs/new/", views.run_new, name="run_new"),
    path("runs/<int:run_id>/", views.run_overview, name="run_overview"),
    path("runs/<int:run_id>/uploads/", views.run_uploads, name="run_uploads"),
    path("runs/<int:run_id>/validation/", views.run_validation, name="run_validation"),
    path("runs/<int:run_id>/results/", views.run_results, name="run_results"),
    path("runs/<int:run_id>/results/rows/", views.run_rows, name="run_rows"),
    path("runs/<int:run_id>/recon/", views.run_recon, name="run_recon"),
    path("runs/<int:run_id>/export/", views.run_export, name="run_export"),
    path("reference-data/", views.reference_data, name="reference_data"),
    path("mappings/", views.mappings, name="mappings"),
    path("curves/", views.curves, name="curves"),
]

