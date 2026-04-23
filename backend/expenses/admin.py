from django.contrib import admin
from .models import Expense


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['description', 'amount', 'category', 'date', 'created_at']
    list_filter = ['category', 'date', 'created_at']
    search_fields = ['description']
    ordering = ['-date', '-created_at']
    readonly_fields = ['id', 'created_at', 'idempotency_key']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'amount', 'category', 'description', 'date')
        }),
        ('System Fields', {
            'fields': ('created_at', 'idempotency_key'),
            'classes': ('collapse',)
        }),
    )
