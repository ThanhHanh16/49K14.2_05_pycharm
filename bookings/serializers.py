from rest_framework import serializers
from .models import Booking, QLDonDat

class BookingSerializer(serializers.ModelSerializer):
    court_name = serializers.CharField(source='court.name', read_only=True)
    court_code = serializers.CharField(source='court.code', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)
    order_id = serializers.PrimaryKeyRelatedField(source='order', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'court', 'court_name', 'court_code',
            'customer_name', 'phone', 'date', 'start_time', 'end_time',
            'total_price', 'status', 'notes', 'order_id',
            'created_at', 'updated_at',
        ]


class QLDonDatSerializer(serializers.ModelSerializer):
    ma_don = serializers.CharField(source='booking_code', read_only=True)
    bookings = BookingSerializer(many=True, read_only=True)

    class Meta:
        model = QLDonDat
        fields = [
            'id', 'ma_don', 'bookings',
            'ten_khach_hang', 'so_dien_thoai',
            'gio_bat_dau', 'gio_ket_thuc',
            'loai_san', 'san_ap_dung',
            'ngay_dat', 'tong_tien',
            'trang_thai_don', 'thanh_toan',
            'ghi_chu', 'created_at', 'updated_at',
        ]


class CourtScheduleSlotSerializer(serializers.Serializer):
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    price = serializers.DecimalField(max_digits=12, decimal_places=0)
    status = serializers.CharField()


class CourtScheduleSerializer(serializers.Serializer):
    court_id = serializers.IntegerField()
    court_code = serializers.CharField()
    court_name = serializers.CharField()
    court_status = serializers.CharField()
    slots = CourtScheduleSlotSerializer(many=True)


class CourtScheduleResponseSerializer(serializers.Serializer):
    date = serializers.DateField()
    court_type_id = serializers.IntegerField()
    court_type_name = serializers.CharField()
    court_type_code = serializers.CharField()
    data = CourtScheduleSerializer(many=True)
