from rest_framework import serializers

from .models import (
    Customer, CourtType, Court, PriceTable, PriceTableCourt,
    PriceTableTimeSlot, Booking, QLDonDat
)


class CustomerSerializer(serializers.ModelSerializer):
    customer_code = serializers.CharField(required=False, read_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(source='full_name', required=False, allow_blank=True)
    phone = serializers.CharField(source='phone_number', required=False, allow_blank=True)
    ghi_chu = serializers.CharField(source='notes', required=False, allow_blank=True)

    class Meta:
        model = Customer
        fields = ['id', 'customer_code', 'full_name', 'phone_number', 'name', 'phone', 'email', 'notes', 'ghi_chu', 'created_at']

    def validate_phone(self, value):
        if not value:
            return value
        customer_id = self.instance.id if self.instance else None
        qs = Customer.objects.filter(phone_number=value)
        if customer_id:
            qs = qs.exclude(id=customer_id)
        if qs.exists():
            raise serializers.ValidationError("Số điện thoại này đã được sử dụng!")
        return value


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
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'code': {'required': False}
        }


class PriceTableSerializer(serializers.ModelSerializer):
    court_type_name = serializers.CharField(source='court_type.name', read_only=True)
    court_type_code = serializers.CharField(source='court_type.code', read_only=True)

    class Meta:
        model = PriceTable
        fields = [
            'id',
            'price_table_code',
            'price_table_name',
            'court_type',
            'court_type_name',
            'court_type_code',
            'apply_scope',
            'effective_date',
            'end_date',
            'applied_days',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'price_table_code': {'required': False}
        }


class PriceTableCourtSerializer(serializers.ModelSerializer):
    court_name = serializers.CharField(source='court.name', read_only=True)
    court_code = serializers.CharField(source='court.code', read_only=True)

    class Meta:
        model = PriceTableCourt
        fields = [
            'id',
            'price_table',
            'court',
            'court_name',
            'court_code',
        ]


class PriceTableTimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceTableTimeSlot
        fields = [
            'id',
            'price_table',
            'start_time',
            'end_time',
            'unit_price',
            'note',
            'order',
        ]


class BookingSerializer(serializers.ModelSerializer):
    court_name = serializers.CharField(source='court.name', read_only=True)
    court_code = serializers.CharField(source='court.code', read_only=True)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=0, read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id',
            'user',
            'court',
            'court_name',
            'court_code',
            'customer_name',
            'phone',
            'date',
            'start_time',
            'end_time',
            'total_price',
            'status',
            'notes',
            'created_at',
            'updated_at',
        ]


class CourtScheduleSlotSerializer(serializers.Serializer):
    """Serializer for court schedule slots"""
    start_time = serializers.TimeField()
    end_time = serializers.TimeField()
    price = serializers.DecimalField(max_digits=12, decimal_places=0)
    status = serializers.CharField()  # 'available', 'booked', 'maintenance'


class CourtScheduleSerializer(serializers.Serializer):
    """Serializer for court schedule"""
    court_id = serializers.IntegerField()
    court_code = serializers.CharField()
    court_name = serializers.CharField()
    court_status = serializers.CharField()
    slots = CourtScheduleSlotSerializer(many=True)


class CourtScheduleResponseSerializer(serializers.Serializer):
    """Serializer for court schedule response"""
    date = serializers.DateField()
    court_type_id = serializers.IntegerField()
    court_type_name = serializers.CharField()
    court_type_code = serializers.CharField()
    data = CourtScheduleSerializer(many=True)


class QLDonDatSerializer(serializers.ModelSerializer):
    class Meta:
        model = QLDonDat
        fields = '__all__'
