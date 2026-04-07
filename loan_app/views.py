from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import (
    LoginView,
    PasswordResetView,
    PasswordResetDoneView,
    PasswordResetConfirmView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Sum, Count
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth import get_user_model
import json
from .forms import (
    UserRegistrationForm,
    UserUpdateForm,
    FarmerProfileForm,
    LoanApplicationForm,
    RepaymentForm,
    NIDUploadForm,
)
from .models import FarmerProfile, LoanApplication, LoanType, Repayment, User


def home(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request, "home.html")


@login_required
def dashboard(request):
    if request.user.role == "Admin" or request.user.is_staff:
        return admin_dashboard(request)
    elif request.user.role == "Bank Officer":
        return bank_officer_dashboard(request)
    else:
        return farmer_dashboard(request)


@login_required
def admin_dashboard(request):
    total_farmers = User.objects.filter(role="Farmer").count()
    total_loans = LoanApplication.objects.count()
    approved_loans = LoanApplication.objects.filter(status="Approved").count()
    pending_loans = LoanApplication.objects.filter(status="Pending").count()
    rejected_loans = LoanApplication.objects.filter(status="Rejected").count()
    total_disbursed = (
        LoanApplication.objects.filter(status="Approved").aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )
    total_repaid = (
        Repayment.objects.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    )

    loans_by_type = (
        LoanApplication.objects.filter(status="Approved")
        .values("loan_type__name")
        .annotate(count=Count("id"))
    )
    loans_by_status = LoanApplication.objects.values("status").annotate(
        count=Count("id")
    )

    recent_loans = LoanApplication.objects.order_by("-created_at")[:5]
    recent_repayments = Repayment.objects.order_by("-payment_date")[:5]

    context = {
        "dashboard_type": "admin",
        "total_farmers": total_farmers,
        "total_loans": total_loans,
        "approved_loans": approved_loans,
        "pending_loans": pending_loans,
        "rejected_loans": rejected_loans,
        "total_disbursed": total_disbursed,
        "total_repaid": total_repaid,
        "loans_by_type": list(loans_by_type),
        "loans_by_status": list(loans_by_status),
        "recent_loans": recent_loans,
        "recent_repayments": recent_repayments,
    }
    return render(request, "dashboard/admin.html", context)


@login_required
def bank_officer_dashboard(request):
    total_farmers = User.objects.filter(role="Farmer").count()
    total_loans = LoanApplication.objects.count()
    approved_loans = LoanApplication.objects.filter(status="Approved").count()
    pending_loans = LoanApplication.objects.filter(status="Pending").count()
    total_disbursed = (
        LoanApplication.objects.filter(status="Approved").aggregate(Sum("amount"))[
            "amount__sum"
        ]
        or 0
    )

    recent_loans = LoanApplication.objects.order_by("-created_at")[:5]
    for loan in recent_loans:
        if loan.risk_score == 0:
            loan.risk_score = loan.calculate_risk_score()
            loan.save(update_fields=["risk_score"])

    context = {
        "dashboard_type": "bank_officer",
        "total_farmers": total_farmers,
        "total_loans": total_loans,
        "approved_loans": approved_loans,
        "pending_loans": pending_loans,
        "total_disbursed": total_disbursed,
        "recent_loans": recent_loans,
    }
    return render(request, "dashboard/bank_officer.html", context)


@login_required
def farmer_dashboard(request):
    my_loans = LoanApplication.objects.filter(farmer=request.user)
    total_loans = my_loans.count()
    approved_loans = my_loans.filter(status="Approved").count()
    pending_loans = my_loans.filter(status="Pending").count()
    total_disbursed = (
        my_loans.filter(status="Approved").aggregate(Sum("amount"))["amount__sum"] or 0
    )

    total_paid = (
        Repayment.objects.filter(loan__farmer=request.user).aggregate(
            Sum("amount_paid")
        )["amount_paid__sum"]
        or 0
    )

    my_loan_amounts = (
        my_loans.filter(status="Approved")
        .values("loan_type__name")
        .annotate(total=Sum("amount"))
    )

    recent_loans = my_loans.order_by("-created_at")[:5]

    try:
        farmer_profile = request.user.farmer_profile
    except FarmerProfile.DoesNotExist:
        farmer_profile = None

    context = {
        "dashboard_type": "farmer",
        "total_loans": total_loans,
        "approved_loans": approved_loans,
        "pending_loans": pending_loans,
        "total_disbursed": total_disbursed,
        "total_paid": total_paid,
        "my_loan_amounts": list(my_loan_amounts),
        "recent_loans": recent_loans,
        "farmer_profile": farmer_profile,
    }
    return render(request, "dashboard/farmer.html", context)


def register(request):
    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful!")
            return redirect_after_login(user)
    else:
        form = UserRegistrationForm()
    return render(request, "registration/register.html", {"form": form})


def user_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.username}!")
            return redirect_after_login(user)
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "registration/login.html")


def user_logout(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect("login")


@login_required
def profile(request):
    if request.method == "POST":
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("profile")
    else:
        form = UserUpdateForm(instance=request.user)
    return render(request, "registration/profile.html", {"form": form})


def redirect_after_login(user):
    if user.role == "Admin":
        return redirect("dashboard")
    elif user.role == "Bank Officer":
        return redirect("dashboard")
    else:
        return redirect("home")


class CustomPasswordResetView(PasswordResetView):
    template_name = "registration/password_reset_form.html"
    email_template_name = "registration/password_reset_email.html"
    success_url = reverse_lazy("password_reset_done")


class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = "registration/password_reset_done.html"


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = "registration/password_reset_confirm.html"
    success_url = reverse_lazy("password_reset_complete")


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = "registration/password_reset_complete.html"


@login_required
def farmer_profile(request):
    profile = getattr(request.user, "farmer_profile", None)
    if not profile:
        messages.warning(request, "Please complete your farmer profile.")
        return redirect("farmer_profile_create")
    return render(
        request, "farmer/profile_view.html", {"profile": profile, "farmer": None}
    )


@login_required
def farmer_profile_view(request, user_id):
    if not (request.user.is_staff or request.user.role == "Bank Officer"):
        messages.error(request, "You do not have permission to view this profile.")
        return redirect("home")

    farmer = get_object_or_404(User, id=user_id, role="Farmer")
    farmer.refresh_from_db()
    profile = getattr(farmer, "farmer_profile", None)
    print(
        f"DEBUG farmer_profile_view: farmer={farmer.id}, nid_verified={farmer.nid_verified}"
    )
    return render(
        request, "farmer/profile_view.html", {"profile": profile, "farmer": farmer}
    )


@login_required
def farmer_profile_create(request):
    if hasattr(request.user, "farmer_profile"):
        messages.info(request, "You already have a profile.")
        return redirect("farmer_profile")

    if request.method == "POST":
        form = FarmerProfileForm(request.POST, request.FILES)
        if form.is_valid():
            profile = form.save(commit=False)
            profile.user = request.user
            profile.save()
            messages.success(request, "Farmer profile created successfully!")
            return redirect("farmer_profile")
    else:
        form = FarmerProfileForm()
    return render(
        request,
        "farmer/profile_form.html",
        {"form": form, "title": "Create Farmer Profile"},
    )


@login_required
def farmer_profile_update(request):
    profile = get_object_or_404(FarmerProfile, user=request.user)

    if request.method == "POST":
        form = FarmerProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Farmer profile updated successfully!")
            return redirect("farmer_profile")
    else:
        form = FarmerProfileForm(instance=profile)
    return render(
        request,
        "farmer/profile_form.html",
        {"form": form, "title": "Update Farmer Profile"},
    )


@login_required
def upload_document(request):
    if not hasattr(request.user, "farmer_profile"):
        messages.warning(request, "Please complete your farmer profile first.")
        return redirect("farmer_profile_create")

    profile = request.user.farmer_profile

    if request.method == "POST":
        if "land_documents" in request.FILES:
            profile.land_documents = request.FILES["land_documents"]
            profile.save()
            messages.success(request, "Document uploaded successfully!")
        else:
            messages.error(request, "Please select a file to upload.")
        return redirect("farmer_profile")

    return render(request, "farmer/upload_document.html", {"profile": profile})


@login_required
def loan_apply(request):
    if not hasattr(request.user, "farmer_profile"):
        messages.warning(request, "Please complete your farmer profile first.")
        return redirect("farmer_profile_create")

    if hasattr(request.user, "loan_application"):
        messages.warning(request, "You already have a loan application.")
        return redirect("loan_history")

    if request.method == "POST":
        form = LoanApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.farmer = request.user

            application.risk_score = application.calculate_risk_score()
            application.emi = application.calculate_emi()

            if application.risk_score >= 70:
                application.status = "Approved"
            elif application.risk_score < 40:
                application.status = "Rejected"

            application.save()

            if application.risk_score >= 70:
                messages.success(
                    request,
                    f"Loan application submitted and auto-approved! Risk Score: {application.risk_score}",
                )
            elif application.risk_score < 40:
                messages.warning(
                    request,
                    f"Loan application auto-rejected due to low priority score. Risk Score: {application.risk_score}",
                )
            else:
                messages.success(
                    request,
                    f"Loan application submitted successfully! Risk Score: {application.risk_score}",
                )

            return redirect("loan_history")
    else:
        form = LoanApplicationForm()

    loan_types = LoanType.objects.all()
    max_loan_amount = (
        LoanType.objects.aggregate(models.Max("max_amount"))["max_amount__max"] or 0
    )
    return render(
        request,
        "loan/apply.html",
        {"form": form, "loan_types": loan_types, "max_loan_amount": max_loan_amount},
    )


@login_required
def loan_history(request):
    applications = LoanApplication.objects.filter(farmer=request.user).order_by(
        "-created_at"
    )
    for app in applications:
        if app.risk_score == 0:
            app.risk_score = app.calculate_risk_score()
            app.save(update_fields=["risk_score"])
    paginator = Paginator(applications, 10)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "loan/history.html", {"page_obj": page_obj})


@login_required
def loan_detail(request, pk):
    application = get_object_or_404(LoanApplication, pk=pk, farmer=request.user)
    if application.risk_score == 0:
        application.risk_score = application.calculate_risk_score()
        application.save(update_fields=["risk_score"])
    return render(request, "loan/detail.html", {"application": application})


@login_required
def approve_loan(request, pk):
    if not (request.user.is_staff or request.user.role == "Bank Officer"):
        messages.error(request, "You do not have permission to approve loans.")
        return redirect("home")

    application = get_object_or_404(LoanApplication, pk=pk)
    application.risk_score = application.calculate_risk_score()
    application.status = "Approved"
    application.save()
    messages.success(request, f"Loan application #{pk} approved!")
    return redirect("loan_list")


@login_required
def reject_loan(request, pk):
    if not (request.user.is_staff or request.user.role == "Bank Officer"):
        messages.error(request, "You do not have permission to reject loans.")
        return redirect("home")

    application = get_object_or_404(LoanApplication, pk=pk)
    application.risk_score = application.calculate_risk_score()
    application.status = "Rejected"
    application.save()
    messages.success(request, f"Loan application #{pk} rejected!")
    return redirect("loan_list")


@login_required
def loan_list(request):
    if not (request.user.is_staff or request.user.role == "Bank Officer"):
        return redirect("home")

    applications = LoanApplication.objects.all().order_by("-created_at")
    status_filter = request.GET.get("status")
    if status_filter:
        applications = applications.filter(status=status_filter)

    paginator = Paginator(applications, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "loan/list.html",
        {"page_obj": page_obj, "status_filter": status_filter},
    )


@login_required
def make_repayment(request, loan_id):
    loan = get_object_or_404(LoanApplication, pk=loan_id, farmer=request.user)

    if loan.status != "Approved":
        messages.error(request, "Only approved loans can have repayments.")
        return redirect("loan_history")

    repayments = loan.repayments.all()
    total_paid = repayments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    remaining = float(loan.amount) - float(total_paid)

    if remaining <= 0:
        messages.info(request, "This loan has been fully repaid.")
        return redirect("loan_history")

    if request.method == "POST":
        form = RepaymentForm(request.POST, loan=loan)
        if form.is_valid():
            repayment = form.save(commit=False)
            repayment.loan = loan
            repayment.remaining_balance = remaining - float(repayment.amount_paid)
            repayment.save()
            messages.success(request, "Repayment recorded successfully!")
            return redirect("loan_history")
    else:
        form = RepaymentForm(loan=loan)

    return render(
        request,
        "repayment/form.html",
        {"form": form, "loan": loan, "remaining": remaining},
    )


@login_required
def repayment_history(request):
    repayments = Repayment.objects.filter(loan__farmer=request.user).order_by(
        "-payment_date"
    )
    paginator = Paginator(repayments, 15)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    total_repaid = repayments.aggregate(Sum("amount_paid"))["amount_paid__sum"] or 0
    return render(
        request,
        "repayment/history.html",
        {"page_obj": page_obj, "total_repaid": total_repaid},
    )


@login_required
def farmer_list(request):
    if not (request.user.is_staff or request.user.role == "Bank Officer"):
        messages.error(request, "You do not have permission to view farmers.")
        return redirect("home")

    farmers = (
        User.objects.filter(role="Farmer")
        .select_related()
        .prefetch_related("farmer_profile")
    )
    paginator = Paginator(farmers, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "bank_officer/farmer_list.html", {"page_obj": page_obj})


@login_required
def upload_nid(request):
    if request.user.role != "Farmer":
        messages.error(request, "Only farmers can upload NID cards.")
        return redirect("home")

    if request.method == "POST":
        form = NIDUploadForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "NID card uploaded successfully!")
            return redirect("farmer_profile")
    else:
        form = NIDUploadForm(instance=request.user)
    return render(request, "farmer/upload_nid.html", {"form": form})


@login_required
def verify_nid(request, user_id):
    if not (request.user.is_staff or request.user.role == "Bank Officer"):
        messages.error(request, "You do not have permission to verify NID.")
        return redirect("home")

    farmer = get_object_or_404(User, id=user_id, role="Farmer")

    if request.method == "POST":
        action = request.POST.get("action")
        if action == "verify":
            User.objects.filter(id=user_id).update(nid_verified=True, is_verified=True)
            farmer = User.objects.get(id=user_id)
            farmer.nid_verified_by = request.user
            farmer.nid_verified_at = timezone.now()
            farmer.save(update_fields=["nid_verified_by", "nid_verified_at"])
            messages.success(
                request,
                f"NID for {farmer.username} has been verified successfully!",
            )
        elif action == "reject":
            User.objects.filter(id=user_id).update(
                nid_verified=False, is_verified=False
            )
            messages.warning(
                request,
                f"NID for {farmer.username} has been rejected.",
            )
        return redirect("nid_verification_list")

    return render(request, "bank_officer/verify_nid.html", {"farmer": farmer})


@login_required
def nid_verification_list(request):
    if not (request.user.is_staff or request.user.role == "Bank Officer"):
        messages.error(request, "You do not have permission to view this page.")
        return redirect("home")

    farmers = (
        User.objects.filter(role="Farmer")
        .exclude(nid_card_front="")
        .exclude(nid_card_front__isnull=True)
        .order_by("-nid_verified", "-date_joined")
    )
    nid_filter = request.GET.get("nid_status")

    if nid_filter == "verified":
        farmers = farmers.filter(nid_verified=True)
    elif nid_filter == "pending":
        farmers = farmers.filter(nid_verified=False)

    paginator = Paginator(farmers, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "nid_filter": nid_filter,
        "total_farmers_with_nid": User.objects.filter(role="Farmer")
        .exclude(nid_card_front="")
        .exclude(nid_card_front__isnull=True)
        .count(),
        "verified_count": User.objects.filter(role="Farmer", nid_verified=True).count(),
        "pending_count": User.objects.filter(role="Farmer", nid_verified=False)
        .exclude(nid_card_front="")
        .exclude(nid_card_front__isnull=True)
        .count(),
    }
    return render(request, "bank_officer/nid_verification_list.html", context)


@csrf_exempt
@require_http_methods(["POST"])
def farmer_register(request):
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse(
            {"success": False, "message": "Invalid JSON data"}, status=400
        )

    name = data.get("name", "").strip()
    nid_number = data.get("nid_number", "").strip()
    phone = data.get("phone", "").strip()
    email = data.get("email", "").strip()

    if not name:
        return JsonResponse(
            {"success": False, "message": "Name is required"}, status=400
        )

    if not nid_number:
        return JsonResponse(
            {"success": False, "message": "NID number is required"}, status=400
        )

    if not phone:
        return JsonResponse(
            {"success": False, "message": "Phone number is required"}, status=400
        )

    if not email:
        return JsonResponse(
            {"success": False, "message": "Email is required"}, status=400
        )

    if not nid_number.isdigit() or len(nid_number) < 10:
        return JsonResponse(
            {"success": False, "message": "NID must be at least 10 digits"}, status=400
        )

    if not phone.isdigit() or len(phone) < 10:
        return JsonResponse(
            {"success": False, "message": "Phone must be at least 10 digits"},
            status=400,
        )

    if User.objects.filter(nid_number=nid_number).exists():
        return JsonResponse(
            {"success": False, "message": "NID already registered"}, status=400
        )

    if User.objects.filter(phone_number=phone).exists():
        return JsonResponse(
            {"success": False, "message": "Phone number already registered"}, status=400
        )

    if User.objects.filter(email=email).exists():
        return JsonResponse(
            {"success": False, "message": "Email already registered"}, status=400
        )

    try:
        username = f"farmer_{nid_number}"
        base_username = username
        counter = 1
        while User.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        import uuid

        temp_password = str(uuid.uuid4())[:12]

        user = User.objects.create_user(
            username=username,
            email=email,
            password=temp_password,
            first_name=name.split()[0] if name else "",
            last_name=" ".join(name.split()[1:]) if len(name.split()) > 1 else "",
            phone_number=phone,
            nid_number=nid_number,
            role="Farmer",
        )

        return JsonResponse(
            {
                "success": True,
                "message": "Registration Successful",
                "user_id": user.id,
                "username": user.username,
                "temp_password": temp_password,
            },
            status=201,
        )

    except Exception as e:
        return JsonResponse(
            {"success": False, "message": f"Registration failed: {str(e)}"}, status=500
        )
