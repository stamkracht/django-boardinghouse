from django.contrib import admin
from django.core.urlresolvers import reverse_lazy as reverse
from django.utils.translation import ugettext_lazy as _

from .models import Invitation


def status(obj):
    if obj.accepted:
        return True
    if obj.redeemable:
        return None
    return False
status.boolean = True


def expiration(obj):
    if obj.redeemed:
        return ''
    return obj.expires_at


def redemption_code(obj):
    if obj.redeemed:
        return ''
    return '<a href="{0!s}" target=_blank>{1!s}</a>'.format(
        reverse('invite:view', kwargs={'redemption_code': obj.redemption_code}),
        obj.redemption_code
    )
redemption_code.allow_tags = True


class StatusFilter(admin.SimpleListFilter):
    title = _('status')
    parameter_name = 'status'

    def lookups(self, request, model_admin):
        return (
            ('pending', _('Pending')),
            ('expired', _('Expired')),
            ('accepted', _('Accepted')),
            ('declined', _('Declined')),
            ('not_pending', _('Redeemed or Expired')),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value:
            return getattr(queryset, value)()
        return queryset


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = (
        'sender',
        'schema',
        status,
        expiration,
        redemption_code,
    )
    list_filter = (
        StatusFilter,
        'schema',
    )
