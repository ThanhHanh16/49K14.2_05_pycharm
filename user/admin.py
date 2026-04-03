from django.contrib import admin
from .models import (
    Customer, CourtType, Court, PriceTable, PriceTableCourt,
    PriceTableTimeSlot, Booking
)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'phone_number', 'email', 'created_at')
    search_fields = ('full_name', 'phone_number')
    list_filter = ('created_at',)
    ordering = ('-created_at',)


@admin.register(CourtType)
class CourtTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'duration', 'status', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('status', 'duration')
    ordering = ('name',)


@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'court_type', 'area', 'status', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('court_type', 'status', 'area')
    ordering = ('court_type', 'name')


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


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'court', 'date', 'start_time', 'end_time', 'total_price', 'status', 'created_at')
    search_fields = ('customer_name', 'phone', 'court__name')
    list_filter = ('status', 'date', 'court__court_type')
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
