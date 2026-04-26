from django.db.models import Q
from django.contrib.auth import get_user_model
from rest_framework import viewsets, filters, status
from rest_framework.decorators import action, api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth.hashers import make_password
import random
from django.core.mail import send_mail

from accounts.permissions import IsCustomer, IsStaffOrAdmin
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
from rest_framework.permissions import BasePermission, SAFE_METHODS
from datetime import datetime
from accounts.models import CustomerProfile


class IsStaffOrAdminOrReadOnly(BasePermission):
    """
    The request is authenticated as a user, or is a read-only request.
    """

    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS or
            request.user and
            request.user.is_authenticated and (
                request.user.is_staff or request.user.is_superuser
            )
        )


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by('-created_at')
    serializer_class = CustomerSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['full_name', 'phone_number']
    permission_classes = [IsStaffOrAdmin]


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

        # Get courts for this court type (excluding INACTIVE)
        courts = Court.objects.filter(
            court_type=court_type
        ).exclude(status='INACTIVE').prefetch_related('bookings')

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
            'court_type_code': court_type.code,
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
            Q(applied_days=[])
        ).order_by('-effective_date')

        return price_tables.first()

    def _get_day_of_week(self, date_obj):
        """Convert date to day of week string (T2, T3, ..., CN)"""
        days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
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
    permission_classes = [IsStaffOrAdmin]


class PriceTableCourtViewSet(viewsets.ModelViewSet):
    queryset = PriceTableCourt.objects.all()
    serializer_class = PriceTableCourtSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['price_table__price_table_code', 'court__name']
    permission_classes = [IsStaffOrAdmin]


class PriceTableTimeSlotViewSet(viewsets.ModelViewSet):
    queryset = PriceTableTimeSlot.objects.all().order_by('order', 'start_time')
    serializer_class = PriceTableTimeSlotSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['order', 'start_time']
    permission_classes = [IsStaffOrAdmin]


class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().order_by('-date', '-created_at')
    serializer_class = BookingSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['customer_name', 'phone', 'court__name']
    ordering_fields = ['date', 'created_at', 'status']
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Booking.objects.all().order_by('-date', '-created_at')
        return Booking.objects.filter(user=user).order_by('-date', '-created_at')

    @action(detail=False, methods=['post'])
    def create_booking(self, request):
        """
        Create a new booking order with one or more time slots.
        Request body:
        {
            "court_id": 1,
            "customer_name": "Nguyen Van A",
            "phone": "0912345678",
            "date": "2026-04-03",
            "notes": "Optional notes",
            "slots": [  // Optional: List of slots for multi-slot booking
                {"start_time": "07:00", "end_time": "08:00"},
                {"start_time": "12:00", "end_time": "13:00"}
            ],
            "start_time": "07:00", // Fallback for single slot
            "end_time": "08:00"    // Fallback for single slot
        }
        """
        court_id = request.data.get('court_id') or request.data.get('court')
        customer_name = (request.data.get('customer_name') or '').strip() or \
                        request.user.get_full_name() or request.user.username
        phone = (request.data.get('phone') or '').strip()
        date_str = request.data.get('date')
        notes = request.data.get('notes', '')
        
        # Prepare slots list
        slots_data = request.data.get('slots', [])
        if not slots_data:
            start_time_str = request.data.get('start_time')
            end_time_str = request.data.get('end_time')
            if start_time_str and end_time_str:
                slots_data = [{'start_time': start_time_str, 'end_time': end_time_str}]

        # Validations
        if not court_id or not date_str or not slots_data:
            return Response(
                {'error': 'Missing required fields: court_id, date, or slots'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            court = Court.objects.get(id=court_id)
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (Court.DoesNotExist, ValueError) as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        if court.status == 'MAINTENANCE':
            return Response({'error': 'Sân đang bảo trì, không thể đặt.'}, status=status.HTTP_400_BAD_REQUEST)

        if court.status == 'INACTIVE':
            return Response({'error': 'Sân đã ngừng hoạt động, không thể đặt.'}, status=status.HTTP_400_BAD_REQUEST)

        # Create the Order record first
        order = QLDonDat.objects.create(
            ten_khach_hang=customer_name,
            so_dien_thoai=phone,
            ngay_dat=booking_date,
            ghi_chu=notes,
            trang_thai_don='Chờ xác nhận',
            loai_san=court.court_type.name,
            san_ap_dung=court.name,
            tong_tien=0, # Will update after creating bookings
            gio_bat_dau="00:00", # Placeholder
            gio_ket_thuc="00:00"  # Placeholder
        )

        total_price = 0
        min_start = None
        max_end = None
        created_bookings = []

        try:
            for slot in slots_data:
                s_time_str = slot.get('start_time')
                e_time_str = slot.get('end_time')
                
                # Parse times
                try:
                    s_time = datetime.strptime(s_time_str, '%H:%M:%S').time()
                except ValueError:
                    s_time = datetime.strptime(s_time_str, '%H:%M').time()
                    
                try:
                    e_time = datetime.strptime(e_time_str, '%H:%M:%S').time()
                except ValueError:
                    e_time = datetime.strptime(e_time_str, '%H:%M').time()

                # Check overlap
                if Booking.objects.filter(
                    court=court, date=booking_date,
                    start_time__lt=e_time, end_time__gt=s_time
                ).exclude(status='cancelled').exists():
                    raise ValueError(f"Khung giờ {s_time_str}-{e_time_str} đã bị trùng.")

                # Get price
                price_table = self._get_active_price_table(court.court_type, booking_date)
                if not price_table:
                    raise ValueError("Không tìm thấy bảng giá áp dụng.")

                time_slots = PriceTableTimeSlot.objects.filter(
                    price_table=price_table,
                    start_time__gte=s_time, end_time__lte=e_time
                )
                if not time_slots.exists():
                    raise ValueError(f"Khung giờ {s_time_str}-{e_time_str} không hợp lệ trong bảng giá.")

                slot_price = sum(ts.unit_price for ts in time_slots)
                
                # Create Booking
                booking = Booking.objects.create(
                    user=request.user,
                    court=court,
                    customer_name=customer_name,
                    phone=phone,
                    date=booking_date,
                    start_time=s_time,
                    end_time=e_time,
                    total_price=slot_price,
                    notes=notes,
                    status='pending',
                    order=order
                )
                created_bookings.append(booking)
                total_price += slot_price
                
                # Track min/max time
                if min_start is None or s_time < min_start: min_start = s_time
                if max_end is None or e_time > max_end: max_end = e_time

            # Update Order with aggregated data
            order.tong_tien = total_price
            order.gio_bat_dau = min_start
            order.gio_ket_thuc = max_end
            order.save()

        except ValueError as e:
            # If any slot fails, delete the partially created order and bookings
            order.delete() # Cascade delete will handle bookings
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = QLDonDatSerializer(order)
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
            Q(applied_days=[])
        ).order_by('-effective_date')

        return price_tables.first()

    def _get_day_of_week(self, date_obj):
        """Convert date to day of week string (T2, T3, ..., CN)"""
        days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
        return days[date_obj.weekday()]


class QLDonDatViewSet(viewsets.ModelViewSet):
    queryset = QLDonDat.objects.all().order_by('-created_at')
    serializer_class = QLDonDatSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['booking_code', 'ten_khach_hang', 'so_dien_thoai']
    ordering_fields = ['ngay_dat', 'created_at', 'trang_thai_don']
    permission_classes = [IsStaffOrAdmin]


@api_view(['POST'])
def forgot_password_api(request):
    email = request.data.get('email')
    if not email:
        return Response({'detail': 'Email is required'}, status=400)
    User = get_user_model()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({'detail': 'User with this email does not exist'}, status=404)
    otp = str(random.randint(100000, 999999))
    # Note: PasswordResetOTP needs to be imported or handled if you use this code.
    # PasswordResetOTP.objects.create(user=user, otp_code=otp)
    send_mail(
        'Mã khôi phục mật khẩu',
        f'Mã OTP của bạn là: {otp}',
        'from@example.com',
        [email],
        fail_silently=False,
    )
    return Response({'detail': 'OTP đã được gửi'})

@api_view(['POST'])
def reset_password_quick(request):
    username = request.data.get('username')
    email = request.data.get('email')
    phone = request.data.get('phone')
    new_password = request.data.get('new_password')
    confirm_password = request.data.get('confirm_password')

    if not all([username, email, phone, new_password, confirm_password]):
        return Response({'detail': 'Vui lòng nhập đầy đủ thông tin'}, status=400)
    if new_password != confirm_password:
        return Response({'detail': 'Mật khẩu xác nhận không khớp'}, status=400)

    User = get_user_model()
    try:
        # Check if the user exists with this username and email
        user = User.objects.get(username=username, email=email)
        
        # In this project, Customer Profile is in accounts app (CustomerProfile),
        # but there is also a Customer model in user app.
        # Since Customer model in user.models doesn't have a direct 'user' Foreign Key,
        # we filter by the 'phone_number' or 'email' provided.
        # However, for authentication, checking if the given phone belongs to this user
        # can be done via the CustomerProfile if they are connected, or just by verifying
        # the phone matches a Customer record with the same email.
        
        # Check if there is a matching CustomerProfile
        customer_profile = CustomerProfile.objects.filter(user=user, phone=phone).first()
        
        # Cập nhật: xoá phần logic tìm Customer qua `get(user=user)` bị sai
        # Chỉ kiểm tra qua phone_number hoặc email của Model Customer (tuỳ nghiệp vụ)
        customer = Customer.objects.filter(email=email, phone_number=phone).first()

        if not customer and not customer_profile:
             return Response({'detail': 'Thông tin xác thực sai (Số điện thoại không khớp).'}, status=400)

        # Update password
        user.password = make_password(new_password)
        user.save()
        return Response({'detail': 'Đổi mật khẩu thành công'})
    except User.DoesNotExist:
        return Response({'detail': 'Thông tin xác thực sai (Không tìm thấy tài khoản).'}, status=400)