from django.contrib import admin

from .models import PestSighting, SightingMedia, SightingStatusHistory


class MediaInline(admin.TabularInline):
    model = SightingMedia
    extra = 0
    readonly_fields = ("content_type", "size_bytes", "uploaded_at")


class HistoryInline(admin.TabularInline):
    model = SightingStatusHistory
    extra = 0
    readonly_fields = ("from_status", "to_status", "changed_by", "changed_at", "note")


@admin.register(PestSighting)
class PestSightingAdmin(admin.ModelAdmin):
    list_display = ("id", "species", "status", "priority", "district", "observed_at", "reporter")
    list_filter = ("status", "priority", "species", "district")
    search_fields = ("description", "street_or_landmark", "suburb_or_postcode")
    inlines = [MediaInline, HistoryInline]
