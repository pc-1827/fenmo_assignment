from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import IntegrityError
import logging

from .models import Expense
from .serializers import ExpenseSerializer, ExpenseCreateSerializer

logger = logging.getLogger(__name__)


@api_view(['GET', 'POST'])
def expenses_collection(request):
    """
    Expense collection endpoint.

    GET /expenses
    - Optional query params:
      - category: filter by category
      - sort=date_desc: newest first (default)

    POST /expenses
    - Body: amount, category, description, date
    - Requires Idempotency-Key header to safely handle retries
    """
    if request.method == 'GET':
        queryset = Expense.objects.all()

        category = request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)

        sort_order = request.query_params.get('sort', 'date_desc')
        if sort_order == 'date_desc':
            queryset = queryset.order_by('-date', '-created_at')
        else:
            queryset = queryset.order_by('date', 'created_at')

        serializer = ExpenseSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    idempotency_key = request.headers.get('Idempotency-Key', '').strip()
    if not idempotency_key:
        return Response(
            {'idempotency_key': ['Idempotency-Key header is required.']},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        existing_expense = Expense.objects.get(idempotency_key=idempotency_key)
        serializer = ExpenseSerializer(existing_expense)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Expense.DoesNotExist:
        pass

    serializer = ExpenseCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        expense = Expense.objects.create(
            **serializer.validated_data,
            idempotency_key=idempotency_key,
        )
        response_serializer = ExpenseSerializer(expense)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    except IntegrityError as error:
        logger.warning("Integrity error creating expense: %s", error)
        try:
            existing_expense = Expense.objects.get(idempotency_key=idempotency_key)
            response_serializer = ExpenseSerializer(existing_expense)
            return Response(response_serializer.data, status=status.HTTP_200_OK)
        except Expense.DoesNotExist:
            return Response(
                {'error': 'Unable to create expense safely.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
    except Exception as error:
        logger.exception("Error creating expense: %s", error)
        return Response(
            {'error': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
