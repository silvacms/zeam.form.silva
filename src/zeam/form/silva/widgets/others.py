# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.schema.interfaces import ITextLine
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from js.jqueryui import jqueryui

from zeam.form.base import DISPLAY
from zeam.form.base.interfaces import IWidget, IWidgetExtractor
from zeam.form.base.markers import NO_VALUE
from zeam.form.base.widgets import WidgetExtractor, FieldWidget
from zeam.form.ztk.customizations import customize
from zeam.form.ztk.interfaces import ICollectionField
from zeam.form.ztk.widgets.collection import newCollectionWidgetFactory
from zeam.form.ztk.widgets.collection import MultiSelectFieldWidget
from zeam.form.ztk.widgets.textline import TextLineField
from zeam.form.ztk.widgets.uri import URIField
from zeam.form.ztk.widgets.object import ObjectField
from zeam.form.ztk.widgets.object import ObjectFieldWidget
from zeam.form.ztk.widgets.choice import ChoiceFieldWidget
from zeam.form.silva.interfaces import ISMIForm

from silva.core import conf as silvaconf
from silva.core.interfaces.adapters import IIconResolver
from silva.fanstatic import need


@customize(origin=ITextLine)
def customize_textline(field):
    field.htmlAttributes['size'] = '40'


class IconDisplayWidget(FieldWidget):
    grok.name('silva.icon')

    def update(self):
        super(IconDisplayWidget, self).update()
        self._content = self.form.getContentData().getContent()
        self.icon = IIconResolver(self.request).get_tag(self._content)


class IconEditDisplayWidget(IconDisplayWidget):
    grok.name('silva.icon.edit')

    screen = 'content'

    def get_smi_form(self):
        form = self.form
        while form is not None and not ISMIForm.providedBy(form):
            form = getattr(form, 'parent', None)
        return form

    def update(self):
        super(IconEditDisplayWidget, self).update()
        self.path = None
        form = self.get_smi_form()
        if form is not None:
            self.path = form.get_content_path(self._content)


class ObjectFieldWidget(ObjectFieldWidget):
    grok.adapts(ObjectField, Interface, Interface)


class DisplayObjectFieldWidget(ObjectFieldWidget):
    grok.name(unicode(DISPLAY))


grok.global_adapter(
    newCollectionWidgetFactory(mode='lines'),
    adapts=(ICollectionField, Interface, Interface),
    provides=IWidget,
    name='lines')

grok.global_adapter(
    newCollectionWidgetFactory(mode='multipickup'),
    adapts=(ICollectionField, Interface, Interface),
    provides=IWidget,
    name='multipickup')

grok.global_adapter(
    newCollectionWidgetFactory(mode='lines', interface=IWidgetExtractor),
    adapts=(ICollectionField, Interface, Interface),
    provides=IWidgetExtractor,
    name='lines')


class LinesWidget(FieldWidget):
    grok.adapts(ICollectionField, TextLineField, Interface, Interface)
    grok.name('lines')

    def __init__(self, field, value_field, form, request):
        super(LinesWidget, self).__init__(field, form, request)

    def valueToUnicode(self, value):
        return u'\n'.join(value)


class LinesURIWidget(LinesWidget):
    grok.adapts(ICollectionField, URIField, Interface, Interface)


class LinesWidgetExtractor(WidgetExtractor):
    grok.adapts(ICollectionField, TextLineField, Interface, Interface)
    grok.name('lines')

    def __init__(self, field, value_field, form, request):
        super(LinesWidgetExtractor, self).__init__(field, form, request)

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
    grok.adapts(ICollectionField, URIField, Interface, Interface)


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
