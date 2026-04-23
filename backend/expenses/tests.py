from datetime import date
from decimal import Decimal

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Expense


class ExpenseApiTests(APITestCase):
    def test_create_expense_with_idempotency_key_is_safe_for_retries(self):
        url = reverse('expenses_collection')
        payload = {
            'amount': '1250.50',
            'category': 'food',
            'description': 'Groceries',
            'date': '2026-04-23',
        }
        headers = {'HTTP_IDEMPOTENCY_KEY': 'retry-safe-001'}

        first_response = self.client.post(url, payload, format='json', **headers)
        second_response = self.client.post(url, payload, format='json', **headers)

        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertEqual(Expense.objects.count(), 1)
        self.assertEqual(first_response.data['id'], second_response.data['id'])

    def test_create_expense_requires_idempotency_key_header(self):
        url = reverse('expenses_collection')
        payload = {
            'amount': '300.00',
            'category': 'transport',
            'description': 'Metro card',
            'date': '2026-04-23',
        }

        response = self.client.post(url, payload, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('idempotency_key', response.data)

    def test_list_expenses_supports_filter_and_date_desc_sort(self):
        Expense.objects.create(
            amount=Decimal('120.00'),
            category='food',
            description='Lunch',
            date=date(2026, 4, 20),
            idempotency_key='list-1',
        )
        Expense.objects.create(
            amount=Decimal('75.00'),
            category='food',
            description='Snacks',
            date=date(2026, 4, 22),
            idempotency_key='list-2',
        )
        Expense.objects.create(
            amount=Decimal('250.00'),
            category='transport',
            description='Cab',
            date=date(2026, 4, 21),
            idempotency_key='list-3',
        )

        url = f"{reverse('expenses_collection')}?category=food&sort=date_desc"
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]['description'], 'Snacks')
        self.assertEqual(response.data[1]['description'], 'Lunch')
