import datetime

from django.apps import AppConfig
from django.core.checks import Error, register


class BoardingHouseDemoConfig(AppConfig):
    name = 'boardinghouse.contrib.demo'

    def ready(self):
        # Make sure our required setting exists.
        from django.conf import settings

        if not hasattr(settings, 'BOARDINGHOUSE_DEMO_PREFIX'):
            settings.BOARDINGHOUSE_DEMO_PREFIX = '__demo_'

        if not hasattr(settings, 'BOARDINGHOUSE_DEMO_PERIOD'):
            settings.BOARDINGHOUSE_DEMO_PERIOD = datetime.timedelta(31)

        # Monkey-patch the TemplateSchema QuerySet
        from boardinghouse.contrib.template.models import SchemaTemplateQuerySet

        def valid_for_demo(self):
            return self.exclude(use_for_demo=None)

        SchemaTemplateQuerySet.valid_for_demo = valid_for_demo

        from boardinghouse.contrib.demo import receivers  # NOQA


@register('settings')
def check_demo_prefix_stats_with_underscore(app_configs=None, **kwargs):
    from django.conf import settings

    if not settings.BOARDINGHOUSE_DEMO_PREFIX.startswith('_'):
        return [Error('BOARDINGHOUSE_DEMO_PREFIX must start with an underscore',
                      id='boardinghouse.contrib.demo.E001')]

    return []


@register('settings')
def check_demo_expiry_is_timedelta(app_configs=None, **kwargs):
    from django.conf import settings

    if not isinstance(settings.BOARDINGHOUSE_DEMO_PERIOD, datetime.timedelta):
        return [Error('BOARDINGHOUSE_DEMO_PERIOD must be a datetime.timedelta() instance',
                      id='boardinghouse.contrib.demo.E002')]

    return []


@register('settings')
def ensure_contrib_template_installed(app_configs=None, **kwargs):
    from django.apps import apps

    if not apps.is_installed('boardinghouse.contrib.template'):
        return [Error('"boardinghouse.contrib.template" must be installed for "boardinghouse.contrib.demo"',
                      id='boardinghouse.contrib.demo.E003')]

    return []
