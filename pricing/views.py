from rest_framework import viewsets, filters, status
from rest_framework.response import Response
from accounts.permissions import IsStaffOrAdmin
from .models import PriceTable, PriceTableCourt, PriceTableTimeSlot
from .serializers import PriceTableSerializer, PriceTableCourtSerializer, PriceTableTimeSlotSerializer
from bookings.models import Booking

class PriceTableViewSet(viewsets.ModelViewSet):
    queryset = PriceTable.objects.all().order_by('-effective_date')
    serializer_class = PriceTableSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['price_table_code', 'price_table_name']
    ordering_fields = ['effective_date', 'created_at']
    permission_classes = [IsStaffOrAdmin]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Kiểm tra xem có bất kỳ booking nào của loại sân này 
        # bắt đầu từ ngày hiệu lực của bảng giá hay không
        has_bookings = Booking.objects.filter(
            court__court_type=instance.court_type,
            date__gte=instance.effective_date
        ).exclude(status='cancelled').exists()

        if has_bookings:
            return Response(
                {'error': f'Không thể xóa bảng giá "{instance.price_table_name}" vì đang có lịch đặt sân áp dụng mức giá này. Vui lòng kiểm tra lại.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

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
