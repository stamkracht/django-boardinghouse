from django.conf import settings
from django.contrib import auth
from django.db import models, connection, transaction
from django.utils.translation import ugettext as _
from django.core.validators import RegexValidator
from django.forms import ValidationError

from model_utils.managers import PassThroughManager

import ensure_installation
import signals

try:
    User = auth.get_user_model()
except:
    # Was getting an error where auth.models could not be found.
    import django.contrib.auth.models
    User = auth.models.User
    

# This is a bit of fancy trickery to stick the property _is_schema_aware
# on every model class, returning False, unless it has been explicitly
# set to True in the model definition (see base.py for examples).

class ClassProperty(property):
    def __get__(self, cls, owner):
        return self.fget.__get__(None, owner)()

def is_schema_aware(cls):
    return cls._meta.auto_created and cls._meta.auto_created._is_schema_aware

models.Model._is_schema_aware = ClassProperty(classmethod(is_schema_aware))

class SchemaQuerySet(models.query.QuerySet):
    def bulk_create(self, *args, **kwargs):
        created = super(SchemaQuerySet, self).bulk_create(*args, **kwargs)
        for schema in created:
            schema.create_schema()
        return created
    
    def mass_create(self, *args):
        self.bulk_create([Schema(name=x, schema=x) for x in args])

class Schema(models.Model):
    """
    The Schema model provides an abstraction for a Postgres schema.
    
    It will take care of creating a cloned copy of the template_schema
    when it is created, and also has the ability to activate and deactivate
    itself (at the start and end of the request cycle would be a good plan).
    
    """
    name = models.CharField(max_length=128, unique=True, help_text=_(u'The display name of the schema.'))
    schema = models.CharField(max_length=36, primary_key=True, unique=True,
        validators=[RegexValidator(
            regex='^[a-z][a-z_]*$',
            message=_(u'May only contain lowercase letters and underscores. Must start with a letter.')
        )],
        help_text=_(u'The internal name of the schema. May not be changed after creation.'),
    )
    users = models.ManyToManyField(User, blank=True, null=True, related_name='schemata')
    
    objects = PassThroughManager.for_queryset_class(SchemaQuerySet)()
    
    class Meta:
        app_label = 'multi_schema'
    
    def __unicode__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        self._meta.get_field_by_name('schema')[0].run_validators(self.schema)
        
        if kwargs.get('force_insert'):
            try:
                Schema.objects.get(schema=self.schema)
            except Schema.DoesNotExist:
                pass
            else:
                raise ValidationError('Schema already in use')
            
            try:
                Schema.objects.get(name=self.name)
            except Schema.DoesNotExist:
                pass
            else:
                raise ValidationError('Schema name already in use')
        else:
            try:
                Schema.objects.get(schema=self.schema)
            except Schema.DoesNotExist:
                raise ValidationError('May not change schema after creation')

        self.create_schema()
        
        return super(Schema, self).save(*args, **kwargs)
        
    def create_schema(self, cursor=None):
        if not cursor:
            cursor = connection.cursor()
        cursor.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name = %s", [self.schema])
        if not cursor.fetchone():
            cursor.execute("SELECT clone_schema('__template__', %s);", [self.schema])
            transaction.commit_unless_managed()
            signals.schema_created.send(sender=self, schema=self.schema)
    
    def activate(self, cursor=None):
        signals.schema_pre_activate.send(sender=self, schema=self.schema)
        (cursor or connection.cursor()).execute('SET search_path TO "%s",public' % self.schema)
        signals.schema_post_activate.send(sender=self, schema=self.schema)
    
    def deactivate(self, cursor=None):
        signals.schema_pre_activate.send(sender=self, schema=None)
        (cursor or connection.cursor()).execute('SET search_path TO "$user",public')
        signals.schema_post_activate.send(sender=self, schema=None)

# An in-memory only template schema.
template_schema = Schema(name="Template Schema", schema="__template__")

# class UserSchema(models.Model):
#     """
#     A relationship between a User and a Schema. A User may be able to
#     access the data from many schemata, and in that case should be
#     provided with tools to do so.
#     
#     See templates/multi_schema/change_schema.html for an example.
#     """
#     user = models.ForeignKey(User, related_name='schemata')
#     schema = models.ForeignKey(Schema, related_name='users')
#     
#     class Meta:
#         app_label = 'multi_schema'
#     
#     def __unicode__(self):
#         return u"%s : %s" % (self.user, self.schema)
