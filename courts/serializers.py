from rest_framework import serializers
from django.utils import timezone
from .models import CourtType, Court
from bookings.models import Booking

class CourtTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtType
        fields = '__all__'
        extra_kwargs = {
            'code': {'required': False}
        }


class CourtSerializer(serializers.ModelSerializer):
    court_type_name = serializers.CharField(source='court_type.name', read_only=True)
    court_type_code = serializers.CharField(source='court_type.code', read_only=True)
    is_busy = serializers.SerializerMethodField()

    class Meta:
        model = Court
        fields = [
            'id',
            'code',
            'name',
            'court_type',
            'court_type_name',
            'court_type_code',
            'area',
            'status',
            'is_busy',
            'created_at',
        ]
        extra_kwargs = {
            'code': {'required': False}
        }

    def get_is_busy(self, obj):
        # Lấy thời gian hiện tại theo múi giờ đã cấu hình (Asia/Ho_Chi_Minh)
        now = timezone.localtime(timezone.now())
        current_time = now.time()
        current_date = now.date()
        
        # Kiểm tra xem có bất kỳ booking nào đang diễn ra ngay bây giờ không
        return Booking.objects.filter(
            court=obj,
            date=current_date,
            start_time__lte=current_time,
            end_time__gt=current_time
        ).exclude(status='cancelled').exists()
