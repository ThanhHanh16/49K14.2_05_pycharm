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
        # Hỗ trợ cả định dạng cũ (court_id, slots) và định dạng mới (booking_items)
        customer_name = request.data.get('customer_name')
        phone = request.data.get('phone')
        date_str = request.data.get('date')
        
        booking_items = request.data.get('booking_items')
        
        # Nếu không có booking_items, thử lấy theo định dạng cũ
        if not booking_items:
            court_id = request.data.get('court_id')
            slots = request.data.get('slots', [])
            if court_id and slots:
                booking_items = [{'court_id': court_id, 'slots': slots}]
        
        if not all([date_str, booking_items]):
            return Response({'error': 'Vui lòng cung cấp đầy đủ thông tin (ngày, danh sách sân/khung giờ)'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            booking_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            now_dt = timezone.localtime(timezone.now())
            today = now_dt.date()
            current_time = now_dt.time()

            # 1. Chặn đặt sân trong quá khứ (Ngày)
            if booking_date < today:
                return Response({'error': 'Không thể đặt sân cho ngày trong quá khứ.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'Ngày không hợp lệ: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Kiểm tra định dạng số điện thoại (10 số)
        if phone:
            clean_phone = "".join(filter(str.isdigit, phone))
            if len(clean_phone) != 10:
                return Response({'error': 'Số điện thoại không hợp lệ. Vui lòng nhập đúng 10 chữ số.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({'error': 'Vui lòng cung cấp số điện thoại.'}, status=status.HTTP_400_BAD_REQUEST)

        all_parsed_bookings = []
        total_price = 0
        court_names = set()
        court_types = set()

        for item in booking_items:
            court_id = item.get('court_id')
            slots_data = item.get('slots', [])
            
            if not court_id or not slots_data:
                continue
                
            try:
                court = Court.objects.get(id=court_id)
            except Court.DoesNotExist:
                return Response({'error': f'Sân ID {court_id} không tồn tại.'}, status=status.HTTP_404_NOT_FOUND)

            court_names.add(court.name)
            court_types.add(court.court_type.name)

            for slot in slots_data:
                try:
                    s_time = datetime.strptime(slot['start_time'], '%H:%M').time()
                    e_time = datetime.strptime(slot['end_time'], '%H:%M').time()
                    
                    # 3. Chặn đặt sân trong quá khứ (Giờ - Nếu là ngày hôm nay)
                    if booking_date == today and s_time < current_time:
                        return Response({'error': f'Khung giờ {slot["start_time"]} đã qua, không thể đặt.'}, status=status.HTTP_400_BAD_REQUEST)

                    # Kiểm tra trùng lịch
                    if Booking.objects.filter(court=court, date=booking_date, start_time=s_time, end_time=e_time).exclude(status='cancelled').exists():
                        return Response({'error': f'Sân {court.name} vào khung giờ {slot["start_time"]} - {slot["end_time"]} đã có người đặt.'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Tìm bảng giá phù hợp
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
                    
                    all_parsed_bookings.append({
                        'court': court,
                        'start_time': s_time,
                        'end_time': e_time,
                        'price': slot_price
                    })
                    total_price += slot_price
                except Exception as e:
                    return Response({'error': f'Dữ liệu khung giờ không hợp lệ cho sân {court.name}: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

        if not all_parsed_bookings:
            return Response({'error': 'Không có khung giờ nào được chọn hợp lệ.'}, status=status.HTTP_400_BAD_REQUEST)

        # Tính toán giờ bao quát của toàn đơn hàng
        min_start = min(b['start_time'] for b in all_parsed_bookings)
        max_end = max(b['end_time'] for b in all_parsed_bookings)

        # Tạo đơn hàng (Order)
        order = QLDonDat.objects.create(
            ten_khach_hang=customer_name or "Khách lẻ",
            so_dien_thoai=phone or "N/A",
            ngay_dat=booking_date,
            loai_san=", ".join(sorted(list(court_types))),
            san_ap_dung=", ".join(sorted(list(court_names))),
            tong_tien=total_price,
            gio_bat_dau=min_start,
            gio_ket_thuc=max_end,
            trang_thai_don='Chờ xác nhận'
        )

        # Tạo các bản ghi Booking chi tiết
        for b in all_parsed_bookings:
            Booking.objects.create(
                user=request.user,
                court=b['court'],
                customer_name=customer_name or "Khách lẻ",
                phone=phone or "N/A",
                date=booking_date,
                start_time=b['start_time'],
                end_time=b['end_time'],
                total_price=b['price'],
                order=order,
                status='pending'
            )
        
        return Response(QLDonDatSerializer(order).data, status=status.HTTP_201_CREATED)

class QLDonDatViewSet(viewsets.ModelViewSet):
    queryset = QLDonDat.objects.all().order_by('-created_at')
    serializer_class = QLDonDatSerializer
    permission_classes = [IsStaffOrAdmin]

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        new_status = request.data.get('trang_thai_don')
        
        if not new_status:
            return super().update(request, *args, **kwargs)

        current_status = instance.trang_thai_don
        
        # Quy tắc: Một khi đã Hủy hoặc Hoàn thành thì không được đổi nữa
        if current_status in ['Hoàn thành', 'HOÀN TẤT', 'Hủy', 'ĐÃ HỦY']:
            return Response(
                {'error': f'Đơn hàng đã ở trạng thái "{current_status}" và đã chốt sổ, không thể thay đổi thêm.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        # Quy tắc bổ sung: Không được nhảy cóc từ Chờ xác nhận sang Hoàn thành (phải qua Xác nhận)
        if current_status == 'Chờ xác nhận' and new_status in ['Hoàn thành', 'HOÀN TẤT']:
            return Response(
                {'error': 'Đơn hàng cần được "Xác nhận" trước khi có thể chuyển sang "Hoàn thành".'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().update(request, *args, **kwargs)

class DashboardStatsAPIView(APIView):
    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        today = timezone.now().date()
        yesterday = today - timezone.timedelta(days=1)
        start_of_month = today.replace(day=1)

        # Doanh thu tính từ các đơn "Đã xác nhận" hoặc "Hoàn thành"
        valid_statuses = ['Đã xác nhận', 'Hoàn thành', 'ĐÃ XÁC NHẬN', 'HOÀN TẤT']
        
        revenue_today = QLDonDat.objects.filter(
            ngay_dat=today, 
            trang_thai_don__in=valid_statuses
        ).aggregate(total=Sum('tong_tien'))['total'] or 0
        
        revenue_yesterday = QLDonDat.objects.filter(
            ngay_dat=yesterday, 
            trang_thai_don__in=valid_statuses
        ).aggregate(total=Sum('tong_tien'))['total'] or 0
        
        revenue_month = QLDonDat.objects.filter(
            ngay_dat__gte=start_of_month, 
            trang_thai_don__in=valid_statuses
        ).aggregate(total=Sum('tong_tien'))['total'] or 0
        
        revenue_by_court = QLDonDat.objects.filter(
            ngay_dat=today, 
            trang_thai_don__in=valid_statuses
        ).values('san_ap_dung').annotate(revenue=Sum('tong_tien'))

        return Response({
            'revenue_today': revenue_today,
            'revenue_yesterday': revenue_yesterday,
            'revenue_month': revenue_month,
            'revenue_by_court': [{'court_name': item['san_ap_dung'], 'revenue': item['revenue']} for item in revenue_by_court]
        })
