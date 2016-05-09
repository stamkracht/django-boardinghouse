from django.contrib import admin
from django.utils.timesince import timesince, timeuntil

from .models import DemoSchema


@admin.register(DemoSchema)
class DemoSchemaAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'expiry_date',
        'valid',
        'expires_in',
        'expired_ago',
    ]

    def valid(self, obj):
        return not obj.expired
    valid.boolean = True

    def expires_in(self, obj):
        if not obj.expired:
            return timeuntil(obj.expiry_date)

    def expired_ago(self, obj):
        if obj.expired:
            return timesince(obj.expiry_date)
