from django.db import models
import uuid


class Expense(models.Model):
    """
    Model for storing expense records.
    
    Uses Decimal for amount to ensure proper handling of currency.
    Includes idempotency_key to prevent duplicate entries from retried requests.
    """
    CATEGORY_CHOICES = [
        ('food', 'Food'),
        ('transport', 'Transport'),
        ('utilities', 'Utilities'),
        ('entertainment', 'Entertainment'),
        ('shopping', 'Shopping'),
        ('healthcare', 'Healthcare'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text="Amount in the local currency"
    )
    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES,
        default='other'
    )
    description = models.CharField(max_length=500, blank=True)
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Idempotency key to handle duplicate requests from retries
    idempotency_key = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text="Used to prevent duplicate expense entries from retried requests"
    )
    
    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['category', '-date']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"{self.description} - {self.amount} ({self.date})"
