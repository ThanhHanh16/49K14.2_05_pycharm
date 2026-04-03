from django.contrib import admin
from .models import LoaiSan, San, BangGia, BangGiaSanApDung, KhungGioBangGia


class KhungGioBangGiaInline(admin.TabularInline):
    model = KhungGioBangGia
    extra = 1


class BangGiaSanApDungInline(admin.TabularInline):
    model = BangGiaSanApDung
    extra = 1


@admin.register(BangGia)
class BangGiaAdmin(admin.ModelAdmin):
    list_display = ('ma_bang_gia', 'ten_bang_gia', 'loai_san', 'pham_vi_ap_dung', 'ngay_hieu_luc', 'ngay_ket_thuc')
    search_fields = ('ma_bang_gia', 'ten_bang_gia')
    list_filter = ('loai_san', 'pham_vi_ap_dung')
    inlines = [BangGiaSanApDungInline, KhungGioBangGiaInline]


admin.site.register(LoaiSan)
admin.site.register(San)
admin.site.register(BangGiaSanApDung)
admin.site.register(KhungGioBangGia)

