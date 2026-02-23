from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models import Sum, Count
from django.utils.html import format_html
from .models import User, FarmerProfile, LoanType, LoanApplication, Repayment


admin.site.site_header = "Smart Agricultural Loan Admin"
admin.site.site_title = "SALS Admin"
admin.site.index_title = "Dashboard"


class LoanApplicationInline(admin.TabularInline):
    model = LoanApplication
    extra = 0
    readonly_fields = ['loan_type', 'amount', 'duration_months', 'risk_score', 'status', 'emi', 'created_at']
    can_delete = False
    fields = ['id', 'loan_type', 'amount', 'duration_months', 'risk_score', 'status', 'emi', 'created_at']
    verbose_name = 'Loan Application'
    verbose_name_plural = 'Loan Applications'

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'phone_number', 'is_staff', 'is_active']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'phone_number']
    list_editable = ['is_active']
    date_hierarchy = 'date_joined'
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'phone_number')}),
    )
    inlines = [LoanApplicationInline]


@admin.register(FarmerProfile)
class FarmerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'land_size', 'crop_type', 'location', 'annual_income', 'created_at']
    list_filter = ['crop_type', 'created_at', 'annual_income']
    search_fields = ['user__username', 'user__email', 'location', 'user__first_name', 'user__last_name']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['user', 'land_size', 'crop_type', 'location', 'annual_income', 'land_documents', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'


@admin.register(LoanType)
class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'interest_rate', 'max_amount', 'description_short', 'created_at']
    list_filter = ['created_at', 'interest_rate']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    fields = ['name', 'interest_rate', 'max_amount', 'description', 'created_at', 'updated_at']
    ordering = ['name']
    date_hierarchy = 'created_at'

    def description_short(self, obj):
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'


@admin.register(LoanApplication)
class LoanApplicationAdmin(admin.ModelAdmin):
    list_display = ['id', 'farmer_link', 'loan_type', 'amount', 'duration_months', 'risk_score', 'status', 'status_badge', 'emi', 'created_at']
    list_filter = ['status', 'loan_type', 'created_at', 'risk_score']
    search_fields = ['farmer__username', 'farmer__email', 'id', 'farmer__first_name', 'farmer__last_name']
    readonly_fields = ['risk_score', 'emi', 'created_at', 'updated_at']
    fields = ['farmer', 'loan_type', 'amount', 'duration_months', 'risk_score', 'status', 'emi', 'created_at', 'updated_at']
    ordering = ['-created_at']
    date_hierarchy = 'created_at'
    list_editable = ['status']
    actions = ['approve_loans', 'reject_loans']

    def farmer_link(self, obj):
        from django.urls import reverse
        return format_html('<a href="{}">{}</a>', reverse('admin:loan_app_user_change', args=[obj.farmer.id]), obj.farmer.username)
    farmer_link.short_description = 'Farmer'

    def status_badge(self, obj):
        colors = {'Pending': 'warning', 'Approved': 'success', 'Rejected': 'danger'}
        color = colors.get(obj.status, 'secondary')
        return format_html('<span class="badge bg-{}">{}</span>', color, obj.status)
    status_badge.short_description = 'Status'

    def approve_loans(self, request, queryset):
        updated = queryset.update(status='Approved')
        self.message_user(request, f'{updated} loan(s) approved.')
    approve_loans.short_description = 'Approve selected loans'

    def reject_loans(self, request, queryset):
        updated = queryset.update(status='Rejected')
        self.message_user(request, f'{updated} loan(s) rejected.')
    reject_loans.short_description = 'Reject selected loans'


@admin.register(Repayment)
class RepaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'loan_link', 'amount_paid', 'remaining_balance', 'payment_date']
    list_filter = ['payment_date', 'loan__status']
    search_fields = ['loan__id', 'loan__farmer__username', 'loan__farmer__email', 'notes']
    readonly_fields = ['payment_date', 'remaining_balance']
    fields = ['loan', 'amount_paid', 'payment_date', 'remaining_balance', 'notes']
    ordering = ['-payment_date']
    date_hierarchy = 'payment_date'

    def loan_link(self, obj):
        from django.urls import reverse
        return format_html('<a href="{}">Loan #{}</a>', reverse('admin:loan_app_loanapplication_change', args=[obj.loan.id]), obj.loan.id)
    loan_link.short_description = 'Loan'
