from django.contrib import admin

from .models import District, PestSpecies, Tag


@admin.register(PestSpecies)
class PestSpeciesAdmin(admin.ModelAdmin):
    list_display = ("common_name", "category", "family", "genus", "is_invasive", "is_active")
    list_filter = ("category", "is_invasive", "is_active")
    search_fields = ("common_name", "scientific_name", "family", "genus")


admin.site.register(District)
admin.site.register(Tag)
