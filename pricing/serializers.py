from rest_framework import serializers
from django.db.models import Q
from .models import PriceTable, PriceTableCourt, PriceTableTimeSlot

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
                            raise serializers.ValidationError("Các khung giờ bị trùng lặp.")

        is_all_courts = data.get('is_all_courts')
        if is_all_courts is not None:
            data['apply_scope'] = 'ALL' if is_all_courts else 'SPECIFIC'
            
        expiry_date = data.get('expiry_date')
        if expiry_date:
            data['end_date'] = expiry_date

        return data

    def create(self, validated_data):
        from datetime import timedelta
        time_slots_data = validated_data.pop('time_slots', [])
        is_all_courts = validated_data.pop('is_all_courts', None)
        expiry_date = validated_data.pop('expiry_date', None)
        court_ids = validated_data.pop('court_ids', [])
        
        price_table = PriceTable.objects.create(**validated_data)
        for slot_data in time_slots_data:
            PriceTableTimeSlot.objects.create(price_table=price_table, **slot_data)
            
        if validated_data.get('apply_scope') == 'SPECIFIC':
            for court_id in court_ids:
                PriceTableCourt.objects.create(price_table=price_table, court_id=court_id)
        return price_table

    def update(self, instance, validated_data):
        time_slots_data = validated_data.pop('time_slots', None)
        court_ids = validated_data.pop('court_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if time_slots_data is not None:
            instance.time_slots.all().delete()
            for slot_data in time_slots_data:
                PriceTableTimeSlot.objects.create(price_table=instance, **slot_data)

        if validated_data.get('apply_scope') == 'SPECIFIC' and court_ids is not None:
            instance.applied_courts.all().delete()
            for court_id in court_ids:
                PriceTableCourt.objects.create(price_table=instance, court_id=court_id)
        return instance
