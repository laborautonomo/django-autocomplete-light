from __future__ import unicode_literals

"""
ChoiceWidget is intended to work as a replacement for django's Select widget,
and MultipleChoiceWidget for django's SelectMultiple.

Constructing a widget needs an Autocomplete class or registered autocomplete
name.

The choice autocomplete widget renders from autocomplete_light/widget.html
template.
"""
import six

from django import forms
from django.forms.util import flatatt
from django.utils import safestring
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from .registry import registry as default_registry

__all__ = ['WidgetBase', 'ChoiceWidget', 'MultipleChoiceWidget', 'TextWidget']


class WidgetBase(object):
    """
    Base widget for autocompletes.

    Mainly handles passing arguments from Python to HTML data-* attributes,
    via widget_js_attributes and autocomplete_js_attributes. Javascript will
    parse these data-* attributes.

    This widget also renders the widget template.
    """

    def __init__(self, autocomplete=None,
                 widget_js_attributes=None, autocomplete_js_attributes=None,
                 extra_context=None, registry=None):

        registry = registry or default_registry
        self.autocomplete = registry.get_autocomplete_from_arg(autocomplete)
        self.widget_js_attributes = widget_js_attributes or {}
        self.autocomplete_js_attributes = autocomplete_js_attributes or {}
        self.extra_context = extra_context or {}

    def process_js_attributes(self):
        extra_autocomplete_js_attributes = getattr(self.autocomplete,
            'autocomplete_js_attributes', {})
        self.autocomplete_js_attributes.update(
            extra_autocomplete_js_attributes)

        extra_widget_js_attributes = getattr(self.autocomplete,
            'widget_js_attributes', {})
        self.widget_js_attributes.update(
            extra_widget_js_attributes)

        if 'bootstrap' not in self.widget_js_attributes.keys():
            self.widget_js_attributes['bootstrap'] = 'normal'

        if 'choice_selector' not in self.autocomplete_js_attributes.keys():
            self.autocomplete_js_attributes['choice_selector'] = '[data-value]'

        if 'url' not in self.autocomplete_js_attributes.keys():
            url = self.autocomplete().get_absolute_url()
            self.autocomplete_js_attributes['url'] = url

        if 'placeholder' not in self.autocomplete_js_attributes.keys():
            self.autocomplete_js_attributes['placeholder'] = _(
                'type some text to search in this autocomplete').capitalize()

    def render(self, name, value, attrs=None):
        final_attrs = self.build_attrs(attrs)
        self.html_id = final_attrs.pop('id', name)

        autocomplete = self.autocomplete(values=value)

        self.process_js_attributes()

        context = {
            'name': name,
            'values': values,
            'widget': self,
            'extra_attrs': safestring.mark_safe(flatatt(final_attrs)),
            'autocomplete': autocomplete,
        }
        context.update(self.extra_context)
        templates = [
            'autocomplete_light/%s/widget.html' %
            self.autocomplete_name.lower(),
            'autocomplete_light/%s/widget.html' % getattr(autocomplete,
                'widget_template_name', ''),
            'autocomplete_light/widget.html',
        ]
        widget_template = getattr(autocomplete, 'widget_template', None)
        if widget_template:
            templates.insert(0, widget_template)
        return safestring.mark_safe(render_to_string(templates, context))


class ChoiceWidget(WidgetBase, forms.Select):
    """
    Widget that provides an autocomplete for zero to one choice.
    """

    def __init__(self, autocomplete=None,
                 widget_js_attributes=None, autocomplete_js_attributes=None,
                 extra_context=None, registry=None, *args, **kwargs):

        forms.Select.__init__(self, *args, **kwargs)

        WidgetBase.__init__(self, autocomplete,
            widget_js_attributes, autocomplete_js_attributes, extra_context)

        self.widget_js_attributes['max_values'] = 1


class MultipleChoiceWidget(WidgetBase, forms.SelectMultiple):
    """
    Widget that provides an autocomplete for zero to n choices.
    """
    def __init__(self, autocomplete=None,
                 widget_js_attributes=None, autocomplete_js_attributes=None,
                 extra_context=None, registry=None, *args, **kwargs):
        forms.SelectMultiple.__init__(self, *args, **kwargs)

        WidgetBase.__init__(self, autocomplete,
            widget_js_attributes, autocomplete_js_attributes, extra_context)


class TextWidget(forms.TextInput, WidgetBase):
    """ Widget that just adds an autocomplete to fill a text input """

    def __init__(self, autocomplete=None,
                 widget_js_attributes=None, autocomplete_js_attributes=None,
                 extra_context=None, *args, **kwargs):

        forms.TextInput.__init__(self, *args, **kwargs)

        WidgetBase.__init__(self, autocomplete,
            widget_js_attributes, autocomplete_js_attributes)

    def build_attrs(self, extra_attrs=None, **kwargs):
        attrs = forms.TextInput.build_attrs(self, extra_attrs, **kwargs)

        def update_attrs(source, prefix=''):
            for key, value in source.items():
                key = u'data-%s%s' % (prefix, key.replace('_', '-'))
                attrs[key] = value

        self.process_js_attributes()
        update_attrs(self.widget_js_attributes)
        update_attrs(self.autocomplete_js_attributes, 'autocomplete-')

        if 'class' not in attrs.keys():
            attrs['class'] = ''
        attrs['class'] += ' autocomplete-light-text-widget'

        return attrs
