# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from js.jqueryui import jqueryui

from zeam.form.base.interfaces import IWidget, IWidgetExtractor
from zeam.form.base.markers import NO_VALUE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaFieldWidget
from zeam.form.ztk.interfaces import ICollectionSchemaField
from zeam.form.ztk.widgets.collection import newCollectionWidgetFactory
from zeam.form.ztk.widgets.collection import MultiSelectFieldWidget
from zeam.form.ztk.widgets.textline import TextLineSchemaField
from zeam.form.ztk.widgets.uri import URISchemaField
from zeam.form.ztk.widgets.object import ObjectSchemaField
from zeam.form.ztk.widgets.object import ObjectFieldWidget
from zeam.form.ztk.widgets.choice import ChoiceFieldWidget
from zeam.form.silva.interfaces import ISMIForm

from silva.core import conf as silvaconf
from silva.core.interfaces.adapters import IIconResolver
from silva.fanstatic import need


class IconDisplayWidget(SchemaFieldWidget):
    grok.name('silva.icon')

    def update(self):
        super(IconDisplayWidget, self).update()
        self._content = self.form.getContentData().getContent()
        self.icon = IIconResolver(self.request).get_tag(self._content)


class IconEditDisplayWidget(IconDisplayWidget):
    grok.name('silva.icon.edit')

    def update(self):
        super(IconEditDisplayWidget, self).update()
        self.path = None
        form = self.form
        while form is not None and not ISMIForm.providedBy(form):
            form = getattr(form, 'parent', None)
        if form is not None:
            self.path = form.get_content_path(self._content)


class ObjectFieldWidget(ObjectFieldWidget):
    grok.adapts(ObjectSchemaField, Interface, Interface)


grok.global_adapter(
    newCollectionWidgetFactory(mode='lines'),
    adapts=(ICollectionSchemaField, Interface, Interface),
    provides=IWidget,
    name='lines')

grok.global_adapter(
    newCollectionWidgetFactory(mode='multipickup'),
    adapts=(ICollectionSchemaField, Interface, Interface),
    provides=IWidget,
    name='multipickup')

grok.global_adapter(
    newCollectionWidgetFactory(mode='lines', interface=IWidgetExtractor),
    adapts=(ICollectionSchemaField, Interface, Interface),
    provides=IWidgetExtractor,
    name='lines')


class LinesWidget(SchemaFieldWidget):
    grok.adapts(
        ICollectionSchemaField, TextLineSchemaField, Interface, Interface)
    grok.name('lines')

    def __init__(self, field, value_field,form, request):
        super(LinesWidget, self).__init__(field, form, request)
        self.text_component = value_field

    def valueToUnicode(self, value):
        return u'\n'.join(value)


class LinesURIWidget(LinesWidget):
    grok.adapts(ICollectionSchemaField, URISchemaField, Interface, Interface)


class LinesWidgetExtractor(WidgetExtractor):
    grok.adapts(
        ICollectionSchemaField, TextLineSchemaField, Interface, Interface)
    grok.name('lines')

    def __init__(self, field, value_field,form, request):
        super(LinesWidgetExtractor, self).__init__(field, form, request)
        self.text_component = value_field

    def extract(self):
        value, errors = super(LinesWidgetExtractor, self).extract()
        if errors is None:
            if value is not NO_VALUE:
                value = self.component.collectionType(
                    filter(lambda v: v,
                           map(lambda s: s.strip('\r'),
                               value.split('\n'))))
        return (value, errors)


class LinesURIWidgetExtractor(LinesWidgetExtractor):
    grok.adapts(ICollectionSchemaField, URISchemaField, Interface, Interface)


class IMultiPickupFieldResources(IDefaultBrowserLayer):
    silvaconf.resource(jqueryui)
    silvaconf.resource('jquery.multiselect.js')
    silvaconf.resource('multipickup.js')


class MultiPickupFieldWidget(MultiSelectFieldWidget):
    grok.name('multipickup')

    def update(self):
        need(IMultiPickupFieldResources)
        super(MultiPickupFieldWidget, self).update()

    def htmlClass(self):
        return (super(MultiPickupFieldWidget, self).htmlClass() +
                ' field-multipickup')


class IComboBoxResources(IDefaultBrowserLayer):
    silvaconf.resource(jqueryui)
    silvaconf.resource('combobox.js')


class ComboBoxFieldWidget(ChoiceFieldWidget):
    grok.name('combobox')

    def update(self):
        need(IComboBoxResources)
        super(ComboBoxFieldWidget, self).update()
