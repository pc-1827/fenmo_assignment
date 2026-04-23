from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from django.db.utils import OperationalError
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint for monitoring backend availability.
    
    Returns:
    - 200 OK if backend is healthy
    - 503 Service Unavailable if database is unreachable
    """
    try:
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        
        return Response(
            {
                'status': 'healthy',
                'message': 'Backend is operational',
            },
            status=status.HTTP_200_OK,
        )
    except OperationalError:
        return Response(
            {
                'status': 'unhealthy',
                'message': 'Database connection failed',
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
    except Exception as error:
        return Response(
            {
                'status': 'unhealthy',
                'message': str(error),
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )
