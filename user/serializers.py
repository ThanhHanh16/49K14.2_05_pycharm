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
            'updated_at',
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

    def validate(self, data):
        start_time = data.get('start_time', self.instance.start_time if self.instance else None)
        end_time = data.get('end_time', self.instance.end_time if self.instance else None)
        
        if start_time and end_time and end_time <= start_time:
            raise serializers.ValidationError("Giờ kết thúc phải lớn hơn giờ bắt đầu.")
            
        price_table = data.get('price_table', self.instance.price_table if self.instance else None)
        
        if price_table and start_time and end_time:
            overlaps = PriceTableTimeSlot.objects.filter(
                price_table=price_table,
                start_time__lt=end_time,
                end_time__gt=start_time
            )
            if self.instance:
                overlaps = overlaps.exclude(id=self.instance.id)
                
            if overlaps.exists():
                overlap_slots = ", ".join([f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}" for slot in overlaps])
                raise serializers.ValidationError(
                    f"Khung giờ này ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}) bị trùng lặp với các khung giờ sau trong bảng giá: {overlap_slots}"
                )
                
        return data


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
        # Kiểm tra trùng lặp trong danh sách time_slots gửi lên
        time_slots = data.get('time_slots', [])
        for i, slot1 in enumerate(time_slots):
            st1 = slot1.get('start_time')
            et1 = slot1.get('end_time')
            for j, slot2 in enumerate(time_slots):
                if i != j:
                    st2 = slot2.get('start_time')
                    et2 = slot2.get('end_time')
                    if st1 and et1 and st2 and et2:
                        if st1 < et2 and st2 < et1:
                            st1_str = st1.strftime('%H:%M') if hasattr(st1, 'strftime') else str(st1)
                            et1_str = et1.strftime('%H:%M') if hasattr(et1, 'strftime') else str(et1)
                            st2_str = st2.strftime('%H:%M') if hasattr(st2, 'strftime') else str(st2)
                            et2_str = et2.strftime('%H:%M') if hasattr(et2, 'strftime') else str(et2)
                            raise serializers.ValidationError(
                                f"Các khung giờ bạn vừa nhập bị trùng lặp thời gian với nhau: {st1_str}-{et1_str} và {st2_str}-{et2_str}."
                            )

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
        
    def update(self, instance, validated_data):
        time_slots_data = validated_data.pop('time_slots', None)
        is_all_courts = validated_data.pop('is_all_courts', None)
        expiry_date = validated_data.pop('expiry_date', None)
        court_ids = validated_data.pop('court_ids', None)

        if is_all_courts is not None:
            validated_data['apply_scope'] = 'ALL' if is_all_courts else 'SPECIFIC'
            
        if expiry_date is not None:
            validated_data['end_date'] = expiry_date

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Cập nhật time_slots
        if time_slots_data is not None:
            # Lấy danh sách ID của time_slots được gửi lên (để giữ lại)
            time_slot_ids = [item.get('id') for item in time_slots_data if item.get('id')]
            
            # Kiểm tra trùng lặp cho các slot sẽ được lưu
            for idx, slot_data in enumerate(time_slots_data):
                start_time = slot_data.get('start_time')
                end_time = slot_data.get('end_time')
                
                if start_time and end_time:
                    # Truy vấn các time slot khác TRONG database (những cái sẽ không bị xóa)
                    # nhưng loại trừ chính nó (nếu nó đã có ID)
                    other_slots_query = instance.time_slots.filter(
                        id__in=time_slot_ids,
                        start_time__lt=end_time,
                        end_time__gt=start_time
                    )
                    
                    if slot_data.get('id'):
                         other_slots_query = other_slots_query.exclude(id=slot_data.get('id'))
                         
                    if other_slots_query.exists():
                        overlap_slots = ", ".join([f"{slot.start_time.strftime('%H:%M')} - {slot.end_time.strftime('%H:%M')}" for slot in other_slots_query])
                        raise serializers.ValidationError(
                             f"Khung giờ ({start_time.strftime('%H:%M')} - {end_time.strftime('%H:%M')}) bị trùng lặp với các khung giờ sau: {overlap_slots}"
                        )
            
            # Xóa các time_slot không có trong danh sách gửi lên
            instance.time_slots.exclude(id__in=time_slot_ids).delete()
            
            for slot_data in time_slots_data:
                slot_id = slot_data.get('id')
                if slot_id:
                    # Cập nhật
                    slot_instance = PriceTableTimeSlot.objects.get(id=slot_id, price_table=instance)
                    for attr, value in slot_data.items():
                        setattr(slot_instance, attr, value)
                    slot_instance.save()
                else:
                    # Tạo mới
                    PriceTableTimeSlot.objects.create(price_table=instance, **slot_data)

        # Cập nhật applied_courts
        if validated_data.get('apply_scope') == 'SPECIFIC' and court_ids is not None:
            # Xóa các sân áp dụng hiện tại
            instance.applied_courts.all().delete()
            # Thêm sân áp dụng mới
            for court_id in court_ids:
                PriceTableCourt.objects.create(price_table=instance, court_id=court_id)
        elif validated_data.get('apply_scope') == 'ALL':
             instance.applied_courts.all().delete()

        return instance


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