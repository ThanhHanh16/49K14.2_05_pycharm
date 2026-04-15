from datetime import datetime

from django.db.models import Q
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import (
    Customer, CourtType, Court, PriceTable, PriceTableCourt,
    PriceTableTimeSlot, Booking, QLDonDat
)
from .serializers import (
    CustomerSerializer, CourtTypeSerializer, CourtSerializer,
    PriceTableSerializer, PriceTableCourtSerializer,
    PriceTableTimeSlotSerializer, BookingSerializer,
    CourtScheduleResponseSerializer, QLDonDatSerializer
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone_number']


class CourtTypeViewSet(viewsets.ModelViewSet):
    queryset = CourtType.objects.filter(status='ACTIVE')
    serializer_class = CourtTypeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'code']
    ordering_fields = ['name', 'created_at']

    @action(detail=False, methods=['get'])
    def schedule(self, request):
        """
        Get court schedule for a specific date and court type
        Query params: date (YYYY-MM-DD), court_type_id

        Response format:
        {
            "date": "2026-04-03",
            "court_type_id": 1,
            "court_type_name": "Sân bóng chuyền",
            "data": [
                {
                    "court_id": 1,
                    "court_code": "CT001",
                    "court_name": "Sân 1",
                    "court_status": "READY",
                    "slots": [
                        {
                            "start_time": "07:00:00",
                            "end_time": "08:00:00",
                            "price": 100000,
                            "status": "available"
                        }
                    ]
                }
            ]
        }
        """
        date_str = request.query_params.get('date')
        court_type_id = request.query_params.get('court_type_id')

        # Validate required parameters
        if not date_str or not court_type_id:
            return Response(
                {'error': 'Missing required parameters: date and court_type_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            court_type = CourtType.objects.get(id=court_type_id)
        except (ValueError, CourtType.DoesNotExist):
            return Response(
                {'error': 'Invalid date format or court_type_id'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get courts for this court type
        courts = Court.objects.filter(court_type=court_type).prefetch_related('bookings')

        court_data = []

        for court in courts:
            # Get active price table for this court type and date
            price_table = self._get_active_price_table(court_type, booking_date)

            if not price_table:
                # No price table found, skip this court
                continue

            # Get time slots for this price table
            time_slots = PriceTableTimeSlot.objects.filter(
                price_table=price_table
            ).order_by('order', 'start_time')

            slots_data = []

            for slot in time_slots:
                # Check if slot is booked
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
            'data': court_data
        }

        serializer = CourtScheduleResponseSerializer(response_data)
        return Response(serializer.data)

    def _get_active_price_table(self, court_type, booking_date):
        """Get active price table for court type and date"""
        # Get day of week (T2, T3, ..., T7, CN)
        day_of_week = self._get_day_of_week(booking_date)

        # Find active price tables for this court type and date
        price_tables = PriceTable.objects.filter(
            court_type=court_type,
            effective_date__lte=booking_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=booking_date)
        ).filter(
            Q(applied_days__isnull=True) |
            Q(applied_days__icontains=day_of_week) |
            Q(applied_days__len=0)
        ).order_by('-effective_date')

        return price_tables.first()

    def _get_day_of_week(self, date_obj):
        """Convert date to day of week string (T2, T3, ..., CN)"""
        days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
        return days[date_obj.weekday()]

    def _get_slot_status(self, court, booking_date, start_time, end_time):
        """Get status of a time slot"""
        # If court is in maintenance, all slots are maintenance
        if court.status == 'MAINTENANCE':
            return 'maintenance'

        # Check if there's a booking for this slot
        booking_exists = Booking.objects.filter(
            court=court,
            date=booking_date,
            start_time=start_time,
            end_time=end_time
        ).exclude(status='cancelled').exists()

        if booking_exists:
            return 'booked'

        return 'available'


class PriceTableViewSet(viewsets.ModelViewSet):
    queryset = PriceTable.objects.all().order_by('-effective_date')
    serializer_class = PriceTableSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['price_table_code', 'price_table_name']
    ordering_fields = ['effective_date', 'created_at']


class PriceTableCourtViewSet(viewsets.ModelViewSet):
    queryset = PriceTableCourt.objects.all()
    serializer_class = PriceTableCourtSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['price_table__price_table_code', 'court__name']


class PriceTableTimeSlotViewSet(viewsets.ModelViewSet):
    queryset = PriceTableTimeSlot.objects.all().order_by('order', 'start_time')
    serializer_class = PriceTableTimeSlotSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'start_time']


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().order_by('-date', '-created_at')
    serializer_class = BookingSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'phone', 'court__name']
    ordering_fields = ['date', 'created_at', 'status']

    @action(detail=False, methods=['post'])
    def create_booking(self, request):
        """
        Create a new booking
        Request body:
        {
            "court_id": 1,
            "customer_name": "Nguyễn Văn A",
            "phone": "0900000001",
            "date": "2026-04-03",
            "start_time": "07:00",
            "end_time": "08:00",
            "notes": "Optional notes"
        }
        """
        court_id = request.data.get('court_id')
        customer_name = request.data.get('customer_name')
        phone = request.data.get('phone')
        date_str = request.data.get('date')
        start_time_str = request.data.get('start_time')
        end_time_str = request.data.get('end_time')
        notes = request.data.get('notes', '')

        # Validate required fields
        required_fields = ['court_id', 'customer_name', 'phone', 'date', 'start_time', 'end_time']
        missing_fields = [field for field in required_fields if not request.data.get(field)]

        if missing_fields:
            return Response(
                {'error': f'Missing required fields: {", ".join(missing_fields)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            court = Court.objects.get(id=court_id)
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            start_time = datetime.strptime(start_time_str, '%H:%M').time()
            end_time = datetime.strptime(end_time_str, '%H:%M').time()
        except (Court.DoesNotExist, ValueError) as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if court is available
        if court.status == 'MAINTENANCE':
            return Response(
                {'error': 'Court is under maintenance'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if slot is already booked
        existing_booking = Booking.objects.filter(
            court=court,
            date=booking_date,
            start_time=start_time,
            end_time=end_time
        ).exclude(status='cancelled').exists()

        if existing_booking:
            return Response(
                {'error': 'This time slot is already booked'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get price for this slot
        price_table = self._get_active_price_table(court.court_type, booking_date)
        if not price_table:
            return Response(
                {'error': 'No active price table found for this date'},
                status=status.HTTP_400_BAD_REQUEST
            )

        time_slot = PriceTableTimeSlot.objects.filter(
            price_table=price_table,
            start_time=start_time,
            end_time=end_time
        ).first()

        if not time_slot:
            return Response(
                {'error': 'Invalid time slot for this court type'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Create booking
        booking = Booking.objects.create(
            court=court,
            customer_name=customer_name,
            phone=phone,
            date=booking_date,
            start_time=start_time,
            end_time=end_time,
            total_price=time_slot.unit_price,
            notes=notes,
            status='pending'
        )

        serializer = BookingSerializer(booking)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _get_active_price_table(self, court_type, booking_date):
        """Get active price table for court type and date"""
        # Get day of week (T2, T3, ..., T7, CN)
        day_of_week = self._get_day_of_week(booking_date)

        # Find active price tables for this court type and date
        price_tables = PriceTable.objects.filter(
            court_type=court_type,
            effective_date__lte=booking_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=booking_date)
        ).filter(
            Q(applied_days__isnull=True) |
            Q(applied_days__icontains=day_of_week) |
            Q(applied_days__len=0)
        ).order_by('-effective_date')

        return price_tables.first()

    def _get_day_of_week(self, date_obj):
        """Convert date to day of week string (T2, T3, ..., CN)"""
        days = ['CN', 'T2', 'T3', 'T4', 'T5', 'T6', 'T7']
        return days[date_obj.weekday()]


class QLDonDatViewSet(viewsets.ModelViewSet):
    queryset = QLDonDat.objects.all().order_by('-created_at')
    serializer_class = QLDonDatSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['ma_don', 'ten_khach_hang', 'so_dien_thoai']
    ordering_fields = ['ngay_dat', 'created_at', 'trang_thai_don']
