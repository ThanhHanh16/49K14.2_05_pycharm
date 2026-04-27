from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Sum, Q
from datetime import datetime

from accounts.permissions import IsStaffOrAdmin
from .models import Booking, QLDonDat
from .serializers import BookingSerializer, QLDonDatSerializer
from courts.models import Court
from pricing.models import PriceTable, PriceTableTimeSlot

class BookingViewSet(viewsets.ModelViewSet):
    queryset = Booking.objects.all().order_by('-date', '-created_at')
    serializer_class = BookingSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff or user.is_superuser:
            return Booking.objects.all()
        return Booking.objects.filter(user=user)

    @action(detail=False, methods=['post'])
    def create_booking(self, request):
        court_id = request.data.get('court_id')
        customer_name = request.data.get('customer_name')
        phone = request.data.get('phone')
        date_str = request.data.get('date')
        slots_data = request.data.get('slots', [])

        if not all([court_id, date_str, slots_data]):
            return Response({'error': 'Vui lòng cung cấp đầy đủ thông tin (sân, ngày, khung giờ)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            court = Court.objects.get(id=court_id)
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except Exception as e:
            return Response({'error': f'Dữ liệu sân hoặc ngày không hợp lệ: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # Parse slots and check for conflicts
        parsed_slots = []
        for slot in slots_data:
            try:
                s_time = datetime.strptime(slot['start_time'], '%H:%M').time()
                e_time = datetime.strptime(slot['end_time'], '%H:%M').time()
                
                # Kiểm tra trùng lịch ngay tại đây
                if Booking.objects.filter(court=court, date=booking_date, start_time=s_time, end_time=e_time).exclude(status='cancelled').exists():
                    return Response({'error': f'Khung giờ {slot["start_time"]} - {slot["end_time"]} đã có người đặt.'}, status=status.HTTP_400_BAD_REQUEST)
                
                parsed_slots.append((s_time, e_time))
            except Exception as e:
                return Response({'error': f'Định dạng giờ không hợp lệ: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not parsed_slots:
            return Response({'error': 'Không có khung giờ nào được chọn.'}, status=status.HTTP_400_BAD_REQUEST)

        # Tính toán giờ bắt đầu và kết thúc thực tế của đơn hàng
        min_start = min(s[0] for s in parsed_slots)
        max_end = max(s[1] for s in parsed_slots)

        # Tạo đơn hàng (Order)
        order = QLDonDat.objects.create(
            ten_khach_hang=customer_name or "Khách lẻ",
            so_dien_thoai=phone or "N/A",
            ngay_dat=booking_date,
            loai_san=court.court_type.name,
            san_ap_dung=court.name,
            tong_tien=0,
            gio_bat_dau=min_start,
            gio_ket_thuc=max_end,
            trang_thai_don='Chờ xác nhận'
        )

        total_price = 0
        for s_time, e_time in parsed_slots:
            # Tìm giá từ bảng giá
            # Ưu tiên tìm bảng giá phù hợp nhất cho ngày hôm đó
            days = ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN']
            day_of_week = days[booking_date.weekday()]
            
            price_table = PriceTable.objects.filter(
                court_type=court.court_type,
                effective_date__lte=booking_date
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=booking_date)
            ).filter(
                Q(applied_days__icontains=day_of_week) | Q(applied_days=[])
            ).order_by('-effective_date').first()

            slot_price = 0
            if price_table:
                ts = PriceTableTimeSlot.objects.filter(
                    price_table=price_table, 
                    start_time__lte=s_time, 
                    end_time__gte=e_time
                ).first()
                if ts:
                    slot_price = ts.unit_price

            Booking.objects.create(
                user=request.user,
                court=court,
                customer_name=customer_name or "Khách lẻ",
                phone=phone or "N/A",
                date=booking_date,
                start_time=s_time,
                end_time=e_time,
                total_price=slot_price,
                order=order,
                status='pending'
            )
            total_price += slot_price

        order.tong_tien = total_price
        order.save()
        
        return Response(QLDonDatSerializer(order).data, status=status.HTTP_201_CREATED)

class QLDonDatViewSet(viewsets.ModelViewSet):
    queryset = QLDonDat.objects.all().order_by('-created_at')
    serializer_class = QLDonDatSerializer
    permission_classes = [IsStaffOrAdmin]

class DashboardStatsAPIView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)
        start_of_month = today.replace(day=1)

        revenue_today = QLDonDat.objects.filter(ngay_dat=today, trang_thai_don='Hoàn thành').aggregate(total=Sum('tong_tien'))['total'] or 0
        revenue_yesterday = QLDonDat.objects.filter(ngay_dat=yesterday, trang_thai_don='Hoàn thành').aggregate(total=Sum('tong_tien'))['total'] or 0
        revenue_month = QLDonDat.objects.filter(ngay_dat__gte=start_of_month, trang_thai_don='Hoàn thành').aggregate(total=Sum('tong_tien'))['total'] or 0
        
        revenue_by_court = QLDonDat.objects.filter(ngay_dat=today, trang_thai_don='Hoàn thành').values('san_ap_dung').annotate(revenue=Sum('tong_tien'))

        return Response({
            'revenue_today': revenue_today,
            'revenue_yesterday': revenue_yesterday,
            'revenue_month': revenue_month,
            'revenue_by_court': [{'court_name': item['san_ap_dung'], 'revenue': item['revenue']} for item in revenue_by_court]
        })
