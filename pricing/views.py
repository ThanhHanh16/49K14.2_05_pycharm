from rest_framework import viewsets, filters
from accounts.permissions import IsStaffOrAdmin
from .models import PriceTable, PriceTableCourt, PriceTableTimeSlot
from .serializers import PriceTableSerializer, PriceTableCourtSerializer, PriceTableTimeSlotSerializer

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
