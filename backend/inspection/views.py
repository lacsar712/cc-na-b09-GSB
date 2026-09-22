from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from inspection.models import Inspection
from inspection.rules import judge


def _can_write(user) -> bool:
    return user.groups.filter(name="inspector").exists()


def health(_request):
    from django.http import JsonResponse

    return JsonResponse({"status": "ok", "service": "nav-aid-inspection"})


@require_http_methods(["GET", "POST"])
def login_view(request):
    from django.contrib.auth import authenticate, login

    error = ""
    if request.method == "POST":
        user = authenticate(
            request,
            username=request.POST.get("username", "").strip(),
            password=request.POST.get("password", ""),
        )
        if user is None:
            error = "用户名或密码错误"
        else:
            login(request, user)
            return redirect("list")
    return render(request, "login.html", {"error": error})


def logout_view(request):
    from django.contrib.auth import logout

    logout(request)
    return redirect("login")


@login_required
def list_view(request):
    rows = Inspection.objects.all()
    return render(request, "list.html", {"rows": rows, "can_write": _can_write(request.user)})


@login_required
def detail_view(request, pk):
    row = get_object_or_404(Inspection, pk=pk)
    return render(request, "detail.html", {"row": row})


@login_required
def reconcile_view(request):
    mismatches = []
    for row in Inspection.objects.all():
        expected_verdict, expected_note = judge(
            row.measured_cd, row.required_cd, row.bearing_error_deg
        )
        if row.verdict != expected_verdict:
            mismatches.append(
                {
                    "row": row,
                    "expected_verdict": expected_verdict,
                    "expected_note": expected_note,
                }
            )
    return render(
        request,
        "reconcile.html",
        {"mismatches": mismatches, "can_write": _can_write(request.user)},
    )


@login_required
@require_http_methods(["POST"])
def reconcile_fix_view(request, pk):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅巡检员可回写判词")
    row = get_object_or_404(Inspection, pk=pk)
    verdict, note = judge(row.measured_cd, row.required_cd, row.bearing_error_deg)
    row.verdict = verdict
    row.note = note
    row.save(update_fields=["verdict", "note"])
    return redirect("reconcile")


@login_required
@require_http_methods(["GET", "POST"])
def create_view(request):
    if not _can_write(request.user):
        return HttpResponseForbidden("仅巡检员可登记灯光巡检")
    error = ""
    if request.method == "POST":
        try:
            measured = float(request.POST["measured_cd"])
            required = float(request.POST["required_cd"])
            bearing = float(request.POST["bearing_error_deg"])
            code = request.POST["aid_code"].strip()
            if not code:
                raise ValueError("empty")
        except (KeyError, ValueError):
            error = "请填编号和三项数值"
        else:
            verdict, note = judge(measured, required, bearing)
            row = Inspection.objects.create(
                aid_code=code,
                measured_cd=measured,
                required_cd=required,
                bearing_error_deg=bearing,
                verdict=verdict,
                note=note,
                created_by=request.user.username,
            )
            return redirect("detail", pk=row.pk)
    return render(request, "form.html", {"error": error})
