from django.contrib import admin
from .models import CourtType, Court

@admin.register(CourtType)
class CourtTypeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'status', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('status',)
    ordering = ('name',)

@admin.register(Court)
class CourtAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'court_type', 'area', 'status', 'created_at')
    search_fields = ('code', 'name')
    list_filter = ('court_type', 'status', 'area')
    ordering = ('court_type', 'name')
