from rest_framework import serializers
from .models import Customer
from rest_framework import serializers
from .models import LoaiSan, San, BangGia, BangGiaSanApDung, KhungGioBangGia


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class LoaiSanSerializer(serializers.ModelSerializer):
    class Meta:
        model = LoaiSan
        fields = '__all__'


class SanSerializer(serializers.ModelSerializer):
    loai_san_ten = serializers.CharField(source='loai_san.ten_loai_san', read_only=True)

    class Meta:
        model = San
        fields = ['id', 'ma_san', 'ten_san', 'loai_san', 'loai_san_ten', 'dang_hoat_dong']


class KhungGioBangGiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = KhungGioBangGia
        fields = ['id', 'gio_bat_dau', 'gio_ket_thuc', 'don_gia', 'ghi_chu', 'thu_tu']


class BangGiaSanApDungSerializer(serializers.ModelSerializer):
    san_ten = serializers.CharField(source='san.ten_san', read_only=True)
    ma_san = serializers.CharField(source='san.ma_san', read_only=True)

    class Meta:
        model = BangGiaSanApDung
        fields = ['id', 'san', 'san_ten', 'ma_san']


class BangGiaSerializer(serializers.ModelSerializer):
    khung_gio = KhungGioBangGiaSerializer(many=True)
    san_ap_dung = BangGiaSanApDungSerializer(many=True, read_only=True)

    # FE gửi danh sách id sân nếu chọn SPECIFIC
    san_ids = serializers.ListField(
        child=serializers.IntegerField(), write_only=True, required=False
    )

    loai_san_ten = serializers.CharField(source='loai_san.ten_loai_san', read_only=True)

    class Meta:
        model = BangGia
        fields = [
            'id',
            'ma_bang_gia',
            'ten_bang_gia',
            'loai_san',
            'loai_san_ten',
            'pham_vi_ap_dung',
            'ngay_hieu_luc',
            'ngay_ket_thuc',
            'ngay_ap_dung',
            'khung_gio',
            'san_ap_dung',
            'san_ids',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        ngay_hieu_luc = attrs.get('ngay_hieu_luc')
        ngay_ket_thuc = attrs.get('ngay_ket_thuc')

        if ngay_ket_thuc and ngay_hieu_luc and ngay_ket_thuc < ngay_hieu_luc:
            raise serializers.ValidationError("Ngày kết thúc phải lớn hơn hoặc bằng ngày hiệu lực.")

        return attrs

    def create(self, validated_data):
        khung_gio_data = validated_data.pop('khung_gio', [])
        san_ids = validated_data.pop('san_ids', [])

        bang_gia = BangGia.objects.create(**validated_data)

        if bang_gia.pham_vi_ap_dung == 'SPECIFIC':
            for san_id in san_ids:
                BangGiaSanApDung.objects.create(bang_gia=bang_gia, san_id=san_id)

        for index, item in enumerate(khung_gio_data, start=1):
            KhungGioBangGia.objects.create(
                bang_gia=bang_gia,
                thu_tu=item.get('thu_tu', index),
                gio_bat_dau=item['gio_bat_dau'],
                gio_ket_thuc=item['gio_ket_thuc'],
                don_gia=item['don_gia'],
                ghi_chu=item.get('ghi_chu', '')
            )

        return bang_gia

    def update(self, instance, validated_data):
        khung_gio_data = validated_data.pop('khung_gio', None)
        san_ids = validated_data.pop('san_ids', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if san_ids is not None:
            BangGiaSanApDung.objects.filter(bang_gia=instance).delete()
            if instance.pham_vi_ap_dung == 'SPECIFIC':
                for san_id in san_ids:
                    BangGiaSanApDung.objects.create(bang_gia=instance, san_id=san_id)

        if khung_gio_data is not None:
            KhungGioBangGia.objects.filter(bang_gia=instance).delete()
            for index, item in enumerate(khung_gio_data, start=1):
                KhungGioBangGia.objects.create(
                    bang_gia=instance,
                    thu_tu=item.get('thu_tu', index),
                    gio_bat_dau=item['gio_bat_dau'],
                    gio_ket_thuc=item['gio_ket_thuc'],
                    don_gia=item['don_gia'],
                    ghi_chu=item.get('ghi_chu', '')
                )

        return instance