from rest_framework import serializers
from .models import Expense
from decimal import Decimal


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'amount', 'category', 'description', 'date', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def validate_amount(self, value):
        """Ensure amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value
    
    def validate_description(self, value):
        """Ensure description is not just whitespace."""
        if value and not value.strip():
            raise serializers.ValidationError("Description cannot be empty or just whitespace.")
        return value


class ExpenseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating expenses with idempotency support.
    """
    class Meta:
        model = Expense
        fields = ['amount', 'category', 'description', 'date']
    
    def validate_amount(self, value):
        """Ensure amount is positive."""
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        if value > Decimal('99999999.99'):
            raise serializers.ValidationError("Amount is too large.")
        return value
    
    def validate_description(self, value):
        """Ensure description is not just whitespace."""
        if value and not value.strip():
            raise serializers.ValidationError("Description cannot be empty or just whitespace.")
        return value
