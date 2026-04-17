from rest_framework import serializers

from .models import (
    Customer, CourtType, Court, PriceTable, PriceTableCourt,
    PriceTableTimeSlot, Booking, QLDonDat
)


class CustomerSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='full_name')
    phone = serializers.CharField(source='phone_number')

    class Meta:
        model = Customer
        fields = ['id', 'name', 'phone', 'email', 'notes', 'created_at']


class CourtTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = CourtType
        fields = '__all__'


class CourtSerializer(serializers.ModelSerializer):
    court_type_name = serializers.CharField(source='court_type.name', read_only=True)

    class Meta:
        model = Court
        fields = [
            'id',
            'code',
            'name',
            'court_type',
            'court_type_name',
            'area',
            'status',
            'created_at',
            'updated_at',
        ]


class PriceTableSerializer(serializers.ModelSerializer):
    court_type_name = serializers.CharField(source='court_type.name', read_only=True)

    class Meta:
        model = PriceTable
        fields = [
            'id',
            'price_table_code',
            'price_table_name',
            'court_type',
            'court_type_name',
            'apply_scope',
            'effective_date',
            'end_date',
            'applied_days',
            'created_at',
            'updated_at',
        ]


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

    class Meta:
        model = Booking
        fields = [
            'id',
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
    data = CourtScheduleSerializer(many=True)


class QLDonDatSerializer(serializers.ModelSerializer):
    class Meta:
        model = QLDonDat
        fields = '__all__'
