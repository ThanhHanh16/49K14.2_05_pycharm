from django.contrib import admin
from .models import PriceTable, PriceTableCourt, PriceTableTimeSlot

@admin.register(PriceTable)
class PriceTableAdmin(admin.ModelAdmin):
    list_display = ('price_table_code', 'price_table_name', 'court_type', 'effective_date', 'end_date', 'apply_scope')
    search_fields = ('price_table_code', 'price_table_name')
    list_filter = ('court_type', 'apply_scope', 'effective_date')
    ordering = ('-effective_date',)

@admin.register(PriceTableCourt)
class PriceTableCourtAdmin(admin.ModelAdmin):
    list_display = ('price_table', 'court')
    search_fields = ('price_table__price_table_code', 'court__name')
    list_filter = ('price_table',)
    ordering = ('price_table', 'court')

@admin.register(PriceTableTimeSlot)
class PriceTableTimeSlotAdmin(admin.ModelAdmin):
    list_display = ('price_table', 'start_time', 'end_time', 'unit_price', 'order')
    search_fields = ('price_table__price_table_code',)
    list_filter = ('price_table',)
    ordering = ('price_table', 'order', 'start_time')
