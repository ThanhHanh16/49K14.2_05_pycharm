from rest_framework import serializers

from django.db import models
from django.db.models import Q
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
        ]
        extra_kwargs = {
            'code': {'required': False}
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
    unit_price = serializers.FloatField()

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
        extra_kwargs = {
            'price_table': {'required': False}
        }


class PriceTableSerializer(serializers.ModelSerializer):
    court_type_name = serializers.CharField(source='court_type.name', read_only=True)
    court_type_code = serializers.CharField(source='court_type.code', read_only=True)
    time_slots = PriceTableTimeSlotSerializer(many=True, required=False)
    applied_courts = PriceTableCourtSerializer(many=True, read_only=True)
    is_all_courts = serializers.BooleanField(write_only=True, required=False)
    expiry_date = serializers.DateField(write_only=True, required=False)
    court_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)
    updated_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

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
            'is_all_courts',
            'court_ids',
            'effective_date',
            'end_date',
            'expiry_date',
            'applied_days',
            'time_slots',
            'applied_courts',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'price_table_code': {'required': False}
        }

    def validate(self, data):
        # Handle mapping for mapping-friendly fields from Android
        is_all_courts = data.get('is_all_courts')
        if is_all_courts is not None:
            data['apply_scope'] = 'ALL' if is_all_courts else 'SPECIFIC'
            
        expiry_date = data.get('expiry_date')
        if expiry_date:
            data['end_date'] = expiry_date

        court_type = data.get('court_type')
        apply_scope = data.get('apply_scope', 'ALL')
        effective_date = data.get('effective_date')
        end_date = data.get('end_date')
        applied_days = data.get('applied_days', [])
        court_ids = data.get('court_ids', [])
        
        instance_id = self.instance.id if self.instance else None
        
        # Check for overlaps that CANNOT be auto-closed
        # (Overlaps where both have fixed ranges that conflict)
        overlaps = PriceTable.objects.filter(court_type=court_type)
        if instance_id:
            overlaps = overlaps.exclude(id=instance_id)
            
        date_q = Q(effective_date__lte=end_date) if end_date else Q()
        date_q &= Q(end_date__gte=effective_date) & Q(end_date__isnull=False)
        
        # We only block if the existing one HAS an end_date that conflicts with us
        # and we can't easily auto-close it.
        # Actually, let's keep it simple: any overlap with a FIXED-end-date table is a block.
        # Overlap with an OPEN-ended table is allowed (it will be auto-closed in create).
        hard_overlaps = overlaps.filter(date_q)
        
        final_hard_overlaps = []
        for pt in hard_overlaps:
            if set(applied_days) & set(pt.applied_days):
                if apply_scope == 'ALL' or pt.apply_scope == 'ALL':
                    final_hard_overlaps.append(pt)
                else:
                    pt_court_ids = set(pt.applied_courts.values_list('court_id', flat=True))
                    if set(court_ids) & pt_court_ids:
                        final_hard_overlaps.append(pt)
        
        if final_hard_overlaps:
            conflicting_names = ", ".join([pt.price_table_name for pt in final_hard_overlaps])
            raise serializers.ValidationError(
                f"Bảng giá này bị trùng lặp với các bảng giá có thời hạn cố định: {conflicting_names}. Hãy điều chỉnh lại ngày."
            )
            
        return data

    def create(self, validated_data):
        from datetime import timedelta
        
        time_slots_data = validated_data.pop('time_slots', [])
        is_all_courts = validated_data.pop('is_all_courts', None)
        expiry_date = validated_data.pop('expiry_date', None)
        court_ids = validated_data.pop('court_ids', [])
        
        if is_all_courts is not None:
            validated_data['apply_scope'] = 'ALL' if is_all_courts else 'SPECIFIC'
            
        if expiry_date:
            validated_data['end_date'] = expiry_date
            
        effective_date = validated_data.get('effective_date')
        court_type = validated_data.get('court_type')
        apply_scope = validated_data.get('apply_scope')
        applied_days = validated_data.get('applied_days', [])

        # Auto-close old price tables
        # Find price tables of the same type that are "open-ended" or end after new start
        old_tables = PriceTable.objects.filter(
            court_type=court_type,
            effective_date__lt=effective_date
        ).filter(
            Q(end_date__isnull=True) | Q(end_date__gte=effective_date)
        )
        
        day_before = effective_date - timedelta(days=1)
        
        for pt in old_tables:
            # Check for day and scope overlap
            if set(applied_days) & set(pt.applied_days):
                should_close = False
                if apply_scope == 'ALL' or pt.apply_scope == 'ALL':
                    should_close = True
                else:
                    pt_court_ids = set(pt.applied_courts.values_list('court_id', flat=True))
                    if set(court_ids) & pt_court_ids:
                        should_close = True
                
                if should_close:
                    pt.end_date = day_before
                    pt.save()

        price_table = PriceTable.objects.create(**validated_data)
        
        # Create time slots
        for slot_data in time_slots_data:
            PriceTableTimeSlot.objects.create(price_table=price_table, **slot_data)
            
        # Create applied courts if scope is SPECIFIC
        if validated_data.get('apply_scope') == 'SPECIFIC':
            for court_id in court_ids:
                PriceTableCourt.objects.create(price_table=price_table, court_id=court_id)
            
        return price_table


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
    # Expose "ma_don" thay vì "booking_code" để Android map đúng field
    ma_don = serializers.CharField(source='booking_code', read_only=True)

    class Meta:
        model = QLDonDat
        fields = [
            'id', 'booking', 'ma_don',
            'ten_khach_hang', 'so_dien_thoai',
            'gio_bat_dau', 'gio_ket_thuc',
            'loai_san', 'san_ap_dung',
            'ngay_dat', 'tong_tien',
            'trang_thai_don', 'thanh_toan',
            'ghi_chu', 'created_at', 'updated_at',
        ]
