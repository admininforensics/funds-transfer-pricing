from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render

from . import mock_data


def _base_context(*, request: HttpRequest, run_id: int | None = None) -> dict:
    run = mock_data.get_run(run_id) if run_id is not None else None
    return {
        "app_title": "FTP Demo (Blueprint UI)",
        "run": run,
        "breadcrumbs": [],
        "nav": [
            {"label": "Runs", "href": "/runs/", "active": request.path.startswith("/runs/")},
            {"label": "Reference Data", "href": "/reference-data/", "active": request.path.startswith("/reference-data/")},
            {"label": "Mappings", "href": "/mappings/", "active": request.path.startswith("/mappings/")},
            {"label": "Curves", "href": "/curves/", "active": request.path.startswith("/curves/")},
        ],
    }


def home_redirect(request: HttpRequest) -> HttpResponse:
    return redirect("run_dashboard")


def run_dashboard(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Run dashboard"
    ctx["breadcrumbs"] = [{"label": "Runs"}]
    ctx["runs"] = mock_data.list_runs()
    return render(request, "ui/run_dashboard.html", ctx)


def run_new(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Create run"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": "Create run"}]
    ctx["suggested_months"] = ["2026-03", "2026-02", "2026-01"]
    return render(request, "ui/run_new.html", ctx)


def run_overview(request: HttpRequest, run_id: int) -> HttpResponse:
    ctx = _base_context(request=request, run_id=run_id)
    ctx["page_title"] = f"Run overview (Run #{run_id})"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": f"Run #{run_id}"}]
    ctx["stage_links"] = [
        {"label": "Upload files", "href": f"/runs/{run_id}/uploads/", "status": "Pending"},
        {"label": "Validation results", "href": f"/runs/{run_id}/validation/", "status": "Issues found"},
        {"label": "Calculation results", "href": f"/runs/{run_id}/results/", "status": "Not run"},
        {"label": "Reconciliation dashboard", "href": f"/runs/{run_id}/recon/", "status": "N/A"},
        {"label": "Export report", "href": f"/runs/{run_id}/export/", "status": "Disabled"},
    ]
    return render(request, "ui/run_overview.html", ctx)


def run_uploads(request: HttpRequest, run_id: int) -> HttpResponse:
    ctx = _base_context(request=request, run_id=run_id)
    ctx["page_title"] = "Upload files"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": f"Run #{run_id}", "href": f"/runs/{run_id}/"}, {"label": "Uploads"}]
    ctx["uploads"] = mock_data.get_uploads()
    return render(request, "ui/run_uploads.html", ctx)


def run_validation(request: HttpRequest, run_id: int) -> HttpResponse:
    ctx = _base_context(request=request, run_id=run_id)
    ctx["page_title"] = "Validation results"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": f"Run #{run_id}", "href": f"/runs/{run_id}/"}, {"label": "Validation"}]
    ctx["validation"] = mock_data.get_validation()
    return render(request, "ui/run_validation.html", ctx)


def reference_data(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Reference data maintenance"
    ctx["breadcrumbs"] = [{"label": "Reference data"}]
    ctx["assumptions"] = mock_data.list_assumptions()
    return render(request, "ui/reference_data.html", ctx)


def mappings(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "BS-to-IS mapping maintenance"
    ctx["breadcrumbs"] = [{"label": "Mappings"}]
    ctx["mappings"] = mock_data.list_mappings()
    return render(request, "ui/mappings.html", ctx)


def curves(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Curve maintenance"
    ctx["breadcrumbs"] = [{"label": "Curves"}]
    ctx["curves"] = mock_data.get_curves()
    return render(request, "ui/curves.html", ctx)


def run_results(request: HttpRequest, run_id: int) -> HttpResponse:
    ctx = _base_context(request=request, run_id=run_id)
    ctx["page_title"] = "Calculation results"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": f"Run #{run_id}", "href": f"/runs/{run_id}/"}, {"label": "Results"}]
    results = mock_data.get_results()
    ctx["kpis"] = results["kpis"]
    ctx["reporting_groups"] = results["reporting_groups"]
    ctx["currencies"] = results["currencies"]
    return render(request, "ui/run_results.html", ctx)


def run_rows(request: HttpRequest, run_id: int) -> HttpResponse:
    ctx = _base_context(request=request, run_id=run_id)
    ctx["page_title"] = "Row-level drilldown"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": f"Run #{run_id}", "href": f"/runs/{run_id}/"}, {"label": "Results", "href": f"/runs/{run_id}/results/"}, {"label": "Rows"}]
    ctx["rows"] = mock_data.get_results()["rows"]
    return render(request, "ui/run_rows.html", ctx)


def run_recon(request: HttpRequest, run_id: int) -> HttpResponse:
    ctx = _base_context(request=request, run_id=run_id)
    ctx["page_title"] = "Reconciliation / control dashboard"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": f"Run #{run_id}", "href": f"/runs/{run_id}/"}, {"label": "Reconciliation"}]
    ctx["controls"] = mock_data.get_results()["controls"]
    return render(request, "ui/run_recon.html", ctx)


def run_export(request: HttpRequest, run_id: int) -> HttpResponse:
    ctx = _base_context(request=request, run_id=run_id)
    ctx["page_title"] = "Report export"
    ctx["breadcrumbs"] = [{"label": "Runs", "href": "/runs/"}, {"label": f"Run #{run_id}", "href": f"/runs/{run_id}/"}, {"label": "Export"}]
    ctx["formats"] = mock_data.get_results()["formats"]
    return render(request, "ui/run_export.html", ctx)

# Create your views here.
