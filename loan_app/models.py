from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ("Farmer", "Farmer"),
        ("Bank Officer", "Bank Officer"),
        ("Admin", "Admin"),
    ]

    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="Farmer")
    is_approved = models.BooleanField(
        default=False, help_text="For Bank Officers - requires admin approval"
    )
    phone_number = models.CharField(max_length=20, blank=True)
    profile_picture = models.ImageField(
        upload_to="profile_pictures/", blank=True, null=True
    )
    is_verified = models.BooleanField(default=False)
    nid_card_front = models.FileField(
        upload_to="nid_cards/",
        blank=True,
        null=True,
        help_text="Upload NID card front side",
    )
    nid_card_back = models.FileField(
        upload_to="nid_cards/",
        blank=True,
        null=True,
        help_text="Upload NID card back side",
    )
    nid_verified = models.BooleanField(
        default=False, help_text="Whether NID has been verified by bank officer"
    )
    nid_verified_by = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="nid_verifications",
    )
    nid_verified_at = models.DateTimeField(null=True, blank=True)
    nid_number = models.CharField(
        max_length=20,
        blank=True,
        unique=True,
        null=True,
        help_text="National ID number (unique per farmer)",
    )

    def __str__(self):
        return self.username


class FarmerProfile(models.Model):
    CROP_TYPE_CHOICES = [
        ("Rice", "Rice"),
        ("Wheat", "Wheat"),
        ("Corn", "Corn"),
        ("Cotton", "Cotton"),
        ("Soybean", "Soybean"),
        ("Sugarcane", "Sugarcane"),
        ("Vegetables", "Vegetables"),
        ("Fruits", "Fruits"),
        ("Other", "Other"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="farmer_profile"
    )
    land_size = models.DecimalField(
        max_digits=10, decimal_places=2, help_text="Land size in acres"
    )
    crop_type = models.CharField(max_length=50, choices=CROP_TYPE_CHOICES)
    location = models.CharField(max_length=255, help_text="Farm location/address")
    annual_income = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Annual income in BDT"
    )
    land_documents = models.FileField(
        upload_to="farmer_documents/", blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class LoanType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Interest rate in percentage"
    )
    max_amount = models.DecimalField(
        max_digits=12, decimal_places=2, help_text="Maximum loan amount in BDT"
    )
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class LoanApplication(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    farmer = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="loan_application"
    )
    loan_type = models.ForeignKey(
        LoanType, on_delete=models.CASCADE, related_name="applications"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    duration_months = models.IntegerField(help_text="Loan duration in months")
    risk_score = models.IntegerField(
        default=0, help_text="Auto-calculated risk score (0-100)"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    emi = models.DecimalField(
        max_digits=12, decimal_places=2, default=0, help_text="Monthly EMI amount"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.farmer.username} - {self.loan_type.name} - {self.amount}"

    def calculate_emi(self):
        if self.loan_type.interest_rate > 0:
            principal = float(self.amount)
            rate = float(self.loan_type.interest_rate) / 100 / 12
            months = self.duration_months
            if rate > 0:
                emi = (
                    principal
                    * rate
                    * ((1 + rate) ** months)
                    / ((1 + rate) ** months - 1)
                )
            else:
                emi = principal / months
        else:
            emi = float(self.amount) / self.duration_months
        return round(emi, 2)

    def save(self, *args, **kwargs):
        self.risk_score = self.calculate_risk_score()
        self.emi = self.calculate_emi()
        super().save(*args, **kwargs)

    def calculate_risk_score(self):
        try:
            farmer_profile = self.farmer.farmer_profile
            income = float(farmer_profile.annual_income)
            land_size = float(farmer_profile.land_size)

            score = 0

            # POOR FARMER PRIORITY - Lower income = Higher score (max 35 pts)
            if income < 15000:
                score += 35
            elif income < 30000:
                score += 25
            elif income < 50000:
                score += 15
            else:
                score += 5

            # SMALL LAND PRIORITY - Smaller land = Higher score (max 30 pts)
            if land_size < 5:
                score += 30
            elif land_size < 20:
                score += 20
            elif land_size < 50:
                score += 10
            else:
                score += 5

            # LOWER LOAN AMOUNT RELATIVE TO INCOME = Higher score (max 25 pts)
            loan_to_income_ratio = float(self.amount) / income
            if loan_to_income_ratio <= 0.5:
                score += 25
            elif loan_to_income_ratio <= 1.0:
                score += 15
            elif loan_to_income_ratio <= 2.0:
                score += 5
            else:
                score += 0

            # PREVIOUS GOOD REPAYMENT HISTORY BONUS (max 10 pts)
            previous_loans = LoanApplication.objects.filter(
                farmer=self.farmer, status="Approved"
            )
            if previous_loans.exists():
                all_repaid = all(loan.status == "Approved" for loan in previous_loans)
                if all_repaid:
                    score += 10

            return min(score, 100)
        except FarmerProfile.DoesNotExist:
            return 0


def calculate_emi(principal, interest_rate, duration_months):
    if interest_rate > 0:
        rate = float(interest_rate) / 100 / 12
        if rate > 0:
            emi = (
                principal
                * rate
                * ((1 + rate) ** duration_months)
                / ((1 + rate) ** duration_months - 1)
            )
        else:
            emi = principal / duration_months
    else:
        emi = principal / duration_months
    return round(emi, 2)


class Repayment(models.Model):
    loan = models.ForeignKey(
        LoanApplication, on_delete=models.CASCADE, related_name="repayments"
    )
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateTimeField(auto_now_add=True)
    remaining_balance = models.DecimalField(max_digits=12, decimal_places=2)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Repayment #{self.id} - Loan #{self.loan.id}"

    def save(self, *args, **kwargs):
        total_paid = sum(
            self.loan.repayments.exclude(pk=self.pk).values_list(
                "amount_paid", flat=True
            )
        )
        total_paid += self.amount_paid
        self.remaining_balance = float(self.loan.amount) - total_paid
        super().save(*args, **kwargs)
