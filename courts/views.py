from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import BasePermission, SAFE_METHODS
from datetime import datetime
from django.db.models import Q

from .models import CourtType, Court
from .serializers import CourtTypeSerializer, CourtSerializer
from bookings.serializers import CourtScheduleResponseSerializer
from pricing.models import PriceTable, PriceTableTimeSlot
from bookings.models import Booking

class IsStaffOrAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated and (
                request.user.is_staff or request.user.is_superuser
            )
        )

class CourtTypeViewSet(viewsets.ModelViewSet):
    queryset = CourtType.objects.all()
    serializer_class = CourtTypeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']
    permission_classes = [IsStaffOrAdminOrReadOnly]

class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']
    permission_classes = [IsStaffOrAdminOrReadOnly]

    @action(detail=False, methods=['get'])
    def schedule(self, request):
        date_str = request.query_params.get('date')
        court_type_id = request.query_params.get('court_type_id')

        if not date_str or not court_type_id:
            return Response({'error': 'Missing parameters'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            court_type = CourtType.objects.get(id=court_type_id)
        except:
            return Response({'error': 'Invalid data'}, status=status.HTTP_400_BAD_REQUEST)

        courts = Court.objects.filter(court_type=court_type).exclude(status='INACTIVE')
        court_data = []

        for court in courts:
            price_table = self._get_active_price_table(court_type, booking_date)
            if not price_table: continue

            time_slots = PriceTableTimeSlot.objects.filter(price_table=price_table).order_by('order', 'start_time')
            slots_data = []

            for slot in time_slots:
                slot_status = self._get_slot_status(court, booking_date, slot.start_time, slot.end_time)
                slots_data.append({
                    'start_time': slot.start_time,
                    'end_time': slot.end_time,
                    'price': slot.unit_price,
                    'status': slot_status
                })

            court_data.append({
                'court_id': court.id,
                'court_code': court.code,
                'court_name': court.name,
                'court_status': court.status,
                'slots': slots_data
            })

        response_data = {
            'date': booking_date.isoformat(),
            'court_type_id': court_type.id,
            'court_type_name': court_type.name,
            'court_type_code': court_type.code,
            'data': court_data
        }
        return Response(CourtScheduleResponseSerializer(response_data).data)

    def _get_active_price_table(self, court_type, booking_date):
        days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
        day_of_week = days[booking_date.weekday()]
        return PriceTable.objects.filter(
            court_type=court_type,
            effective_date__lte=booking_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=booking_date)
        ).filter(
            Q(applied_days__icontains=day_of_week) | Q(applied_days=[])
        ).order_by('-effective_date').first()

    def _get_slot_status(self, court, booking_date, start_time, end_time):
        if court.status == 'MAINTENANCE': return 'maintenance'
        if Booking.objects.filter(court=court, date=booking_date, start_time=start_time, end_time=end_time).exclude(status='cancelled').exists():
            return 'booked'
        return 'available'
