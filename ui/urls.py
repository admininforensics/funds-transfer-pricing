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
    path("inputs/", views.inputs_home, name="inputs_home"),
    path("inputs/reporting-groups/", views.reporting_groups_list, name="reporting_groups_list"),
    path("reference-data/", views.reference_data, name="reference_data"),
    path("reference-data/input-refdata/", views.input_refdata_list, name="input_refdata_list"),
    path("reference-data/input-refdata/new/", views.input_refdata_new, name="input_refdata_new"),
    path("reference-data/input-refdata/<int:row_id>/edit/", views.input_refdata_edit, name="input_refdata_edit"),
    path("mappings/", views.mappings, name="mappings"),
    path("input-data/consolidated/", views.consolidated_data_list, name="consolidated_data_list"),
    path("curves/", views.curves, name="curves"),
]

