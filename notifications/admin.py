''' Django notifications admin file '''
# -*- coding: utf-8 -*-
from django import forms
from django.contrib import admin
from django.contrib.admin.helpers import ActionForm
from django.utils.translation import gettext_lazy
from notifications.base.admin import AbstractNotificationAdmin
from swapper import load_model

Notification = load_model('notifications', 'Notification')
NotificationTemplate = load_model("notifications", "NotificationTemplate")


def mark_unread(modeladmin, request, queryset):
    queryset.update(unread=True)
mark_unread.short_description = gettext_lazy('Mark selected notifications as unread')


class NotificationAdmin(AbstractNotificationAdmin):
    raw_id_fields = ('recipient',)
    readonly_fields = ('action_object_url', 'actor_object_url', 'target_object_url')
    list_display = ('recipient', 'actor',
                    'level', 'target', 'unread', 'public')
    list_filter = ('level', 'unread', 'public', 'timestamp',)
    actions = [mark_unread]

    def get_queryset(self, request):
        qs = super(NotificationAdmin, self).get_queryset(request)
        return qs.prefetch_related('actor', 'action_object', 'target')

class NotificationTemplateAdmin(admin.ModelAdmin):
    list_display = ('verb', )


# Most of this is stolen from django-import-export :)

class NotificationActionForm(ActionForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = []
        for template in NotificationTemplate.objects.all():
            choices.append((template.slug, template.verb))
        self.fields['template'].choices = choices
    template = forms.ChoiceField(label=_('Notification template'), choices=[], required=False)


class AdminNotifyActionMixin:
    def __init__(self, *args, **kwargs):

        self.action_form = NotificationActionForm
        super().__init__(*args, **kwargs)
        self.actions += (self.notify_action,)

    def notify_action(self, admin_class, request, queryset, *args, **kwargs):
        template_slug = request.POST.get('template')
        template = NotificationTemplate.objects.get(slug=template_slug)
        for reciever in queryset:
            reciever.send_templated_notification(template)
    notify_action.short_description = _("Send notification based on template")

    @property
    def media(self):
        super_media = super().media
        return forms.Media(js=super_media._js + ['notifications/action_templates.js'], css=super_media._css)


admin.site.register(Notification, NotificationAdmin)
admin.site.register(NotificationTemplate, NotificationTemplateAdmin)
