from rest_framework import serializers
from .models import CourtType, Court

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
