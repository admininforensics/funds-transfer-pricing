from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from . import mock_data
from .forms import CurvePointForm, InputRefDataRowForm
from .models import InputRefDataRow
from .models import ReportingGroup
from .models import BsIsMapping
from .models import ConsolidatedDataRow
from .models import CurvePoint
from .models import DataEvent


def _base_context(*, request: HttpRequest, run_id: int | None = None) -> dict:
    run = mock_data.get_run(run_id) if run_id is not None else None
    in_mappings = request.path.startswith("/mappings/") or request.path.startswith("/inputs/") or request.path.startswith("/reference-data/input-refdata/")
    in_input_data = request.path.startswith("/input-data/")
    in_curves = request.path.startswith("/curves/")
    return {
        "app_title": "FTP Demo (Blueprint UI)",
        "run": run,
        "breadcrumbs": [],
        "nav": [
            {"label": "Runs", "href": "/runs/", "active": request.path.startswith("/runs/")},
            {
                "label": "Input data",
                "active": in_input_data,
                "children": [
                    {"label": "Consolidated data", "href": "/input-data/consolidated/", "active": request.path.startswith("/input-data/consolidated/")},
                ],
            },
            {
                "label": "Mappings",
                "active": in_mappings,
                "children": [
                    {"label": "BS-to-IS mappings", "href": "/mappings/", "active": request.path.startswith("/mappings/")},
                    {"label": "Reporting groups", "href": "/inputs/reporting-groups/", "active": request.path.startswith("/inputs/reporting-groups/")},
                    {"label": "Input refdata", "href": "/reference-data/input-refdata/", "active": request.path.startswith("/reference-data/input-refdata/")},
                ],
            },
            {
                "label": "Curves",
                "active": in_curves,
                "children": [
                    {"label": "LCY", "href": "/curves/lcy/", "active": request.path.startswith("/curves/lcy/")},
                    {"label": "FCY", "href": "/curves/fcy/", "active": request.path.startswith("/curves/fcy/")},
                ],
            },
        ],
    }


def home_redirect(request: HttpRequest) -> HttpResponse:
    return redirect("run_dashboard")


def run_dashboard(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Run dashboard"
    ctx["breadcrumbs"] = [{"label": "Runs"}]
    ctx["runs"] = mock_data.list_runs()
    # Monthly progress/status: latest import/recalc timestamps per key table
    latest: dict[str, DataEvent] = {}
    for ev in DataEvent.objects.order_by("-created_at").all()[:200]:
        if ev.table_key not in latest:
            latest[ev.table_key] = ev
    ctx["data_status"] = [
        {"label": "Reporting groups", "key": "reporting_group", "event": latest.get("reporting_group")},
        {"label": "Input refdata", "key": "input_refdata", "event": latest.get("input_refdata")},
        {"label": "Consolidated data", "key": "consolidated_data", "event": latest.get("consolidated_data")},
        {"label": "BS↔IS mapping", "key": "bs_is_mapping", "event": latest.get("bs_is_mapping")},
        {"label": "Curves", "key": "curves", "event": latest.get("curves")},
    ]
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
    ctx["reporting_groups"] = ReportingGroup.objects.order_by("group_type", "account").all()
    return render(request, "ui/reference_data.html", ctx)


def inputs_home(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Inputs"
    ctx["breadcrumbs"] = [{"label": "Inputs"}]
    ctx["inputs"] = [
        {"label": "Reporting groups", "href": "/inputs/reporting-groups/", "count": ReportingGroup.objects.count()},
        {"label": "Input refdata", "href": "/reference-data/input-refdata/", "count": InputRefDataRow.objects.count()},
    ]
    return render(request, "ui/inputs_home.html", ctx)


def reporting_groups_list(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Reporting groups (imported)"
    ctx["breadcrumbs"] = [{"label": "Inputs", "href": "/inputs/"}, {"label": "Reporting groups"}]
    ctx["reporting_groups"] = ReportingGroup.objects.order_by("group_type", "account").all()
    return render(request, "ui/reporting_groups_list.html", ctx)


def input_refdata_list(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Input refdata (imported)"
    ctx["breadcrumbs"] = [{"label": "Reference data", "href": "/reference-data/"}, {"label": "Input refdata"}]

    q = (request.GET.get("q") or "").strip()
    page = max(int(request.GET.get("page") or "1"), 1)
    page_size = 100

    qs = InputRefDataRow.objects.all()
    if q:
        qs = qs.filter(calc_key_1__icontains=q)

    total = qs.count()
    rows = list(qs.order_by("id")[(page - 1) * page_size : page * page_size])
    has_prev = page > 1
    has_next = page * page_size < total

    ctx.update(
        {
            "q": q,
            "page": page,
            "page_size": page_size,
            "total": total,
            "rows": rows,
            "has_prev": has_prev,
            "has_next": has_next,
        }
    )
    return render(request, "ui/input_refdata_list.html", ctx)


def input_refdata_edit(request: HttpRequest, row_id: int) -> HttpResponse:
    row = get_object_or_404(InputRefDataRow, id=row_id)
    ctx = _base_context(request=request)
    ctx["page_title"] = f"Edit input refdata row #{row_id}"
    ctx["breadcrumbs"] = [{"label": "Input refdata", "href": "/reference-data/input-refdata/"}, {"label": f"Row #{row_id}"}]

    if request.method == "POST":
        form = InputRefDataRowForm(request.POST, instance=row)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.recalc()
            updated.save()
            return redirect("/reference-data/input-refdata/")
    else:
        form = InputRefDataRowForm(instance=row)

    ctx["form"] = form
    ctx["row"] = row
    return render(request, "ui/input_refdata_edit.html", ctx)


def input_refdata_new(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Add input refdata row"
    ctx["breadcrumbs"] = [{"label": "Input refdata", "href": "/reference-data/input-refdata/"}, {"label": "Add row"}]

    if request.method == "POST":
        form = InputRefDataRowForm(request.POST)
        if form.is_valid():
            created = form.save(commit=False)
            created.recalc()
            created.save()
            return redirect("/reference-data/input-refdata/")
    else:
        form = InputRefDataRowForm()

    ctx["form"] = form
    return render(request, "ui/input_refdata_new.html", ctx)


def mappings(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "BS-to-IS mapping maintenance"
    ctx["breadcrumbs"] = [{"label": "Mappings"}]

    q = (request.GET.get("q") or "").strip()
    page = max(int(request.GET.get("page") or "1"), 1)
    page_size = 100

    qs = BsIsMapping.objects.all()
    if q:
        qs = qs.filter(balance_sheet__icontains=q).union(qs.filter(prof_and_loss__icontains=q))

    total = qs.count()
    mappings = list(qs.order_by("id")[(page - 1) * page_size : page * page_size])
    has_prev = page > 1
    has_next = page * page_size < total

    ctx.update(
        {
            "mappings": mappings,
            "mappings_count": total,
            "q": q,
            "page": page,
            "page_size": page_size,
            "has_prev": has_prev,
            "has_next": has_next,
        }
    )
    return render(request, "ui/mappings.html", ctx)


def consolidated_data_list(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Consolidated data (imported)"
    ctx["breadcrumbs"] = [{"label": "Input data"}, {"label": "Consolidated data"}]

    q = (request.GET.get("q") or "").strip()
    page = max(int(request.GET.get("page") or "1"), 1)
    page_size = 100

    qs = ConsolidatedDataRow.objects.all()
    if q:
        qs = qs.filter(minor_account__icontains=q).union(qs.filter(trial_balance_name__icontains=q))

    total = qs.count()
    rows = list(qs.order_by("row_number")[(page - 1) * page_size : page * page_size])
    has_prev = page > 1
    has_next = page * page_size < total

    ctx.update(
        {
            "q": q,
            "page": page,
            "page_size": page_size,
            "total": total,
            "rows": rows,
            "has_prev": has_prev,
            "has_next": has_next,
        }
    )
    return render(request, "ui/consolidated_data_list.html", ctx)


def curves(request: HttpRequest) -> HttpResponse:
    return redirect("/curves/lcy/")


def curves_lcy(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Curves · LCY"
    ctx["breadcrumbs"] = [{"label": "Curves"}, {"label": "LCY"}]
    ctx["currency"] = "LCY"
    ctx["base_points"] = CurvePoint.objects.filter(currency="LCY", component="BASE").order_by("tenor_days")
    ctx["spread_points"] = CurvePoint.objects.filter(currency="LCY", component="SPREAD").order_by("tenor_days")
    return render(request, "ui/curves_currency.html", ctx)


def curves_fcy(request: HttpRequest) -> HttpResponse:
    ctx = _base_context(request=request)
    ctx["page_title"] = "Curves · FCY"
    ctx["breadcrumbs"] = [{"label": "Curves"}, {"label": "FCY"}]
    ctx["currency"] = "FCY"
    ctx["base_points"] = CurvePoint.objects.filter(currency="FCY", component="BASE").order_by("tenor_days")
    ctx["spread_points"] = CurvePoint.objects.filter(currency="FCY", component="SPREAD").order_by("tenor_days")
    return render(request, "ui/curves_currency.html", ctx)


def curve_point_new(request: HttpRequest, currency: str, component: str) -> HttpResponse:
    currency = currency.upper()
    component = component.upper()

    ctx = _base_context(request=request)
    ctx["page_title"] = f"Add curve point · {currency} · {component}"
    ctx["breadcrumbs"] = [{"label": "Curves", "href": f"/curves/{currency.lower()}/"}, {"label": "Add point"}]

    if request.method == "POST":
        form = CurvePointForm(request.POST)
        if form.is_valid():
            point = form.save(commit=False)
            point.currency = currency
            point.component = component
            point.save()
            return redirect(f"/curves/{currency.lower()}/")
    else:
        form = CurvePointForm()

    ctx["form"] = form
    ctx["currency"] = currency
    ctx["component"] = component
    return render(request, "ui/curve_point_form.html", ctx)


def curve_point_edit(request: HttpRequest, point_id: int) -> HttpResponse:
    point = get_object_or_404(CurvePoint, id=point_id)
    ctx = _base_context(request=request)
    ctx["page_title"] = f"Edit curve point · {point.currency} · {point.component}"
    ctx["breadcrumbs"] = [{"label": "Curves", "href": f"/curves/{point.currency.lower()}/"}, {"label": f"{point.tenor_days}d"}]

    if request.method == "POST":
        form = CurvePointForm(request.POST, instance=point)
        if form.is_valid():
            form.save()
            return redirect(f"/curves/{point.currency.lower()}/")
    else:
        form = CurvePointForm(instance=point)

    ctx["form"] = form
    ctx["point"] = point
    return render(request, "ui/curve_point_form.html", ctx)


def curve_point_delete(request: HttpRequest, point_id: int) -> HttpResponse:
    point = get_object_or_404(CurvePoint, id=point_id)
    if request.method != "POST":
        return redirect(f"/curves/{point.currency.lower()}/")
    currency = point.currency
    point.delete()
    return redirect(f"/curves/{currency.lower()}/")


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
