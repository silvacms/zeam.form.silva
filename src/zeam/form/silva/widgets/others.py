# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import Interface

from zeam.form.base.interfaces import IWidget, IWidgetExtractor
from zeam.form.base.markers import NO_VALUE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaFieldWidget
from zeam.form.ztk.interfaces import ICollectionSchemaField
from zeam.form.ztk.widgets.collection import newCollectionWidgetFactory
from zeam.form.ztk.widgets.textline import TextLineSchemaField

from Products.Silva.icon import get_icon_url


class IconDisplayWidget(SchemaFieldWidget):
    grok.name('silva.icon')

    def update(self):
        super(IconDisplayWidget, self).update()
        content = self.form.getContentData().getContent()
        self.icon_url = get_icon_url(content, self.request)


grok.global_adapter(
    newCollectionWidgetFactory(mode='lines'),
    adapts=(ICollectionSchemaField, Interface, Interface),
    provides=IWidget,
    name='lines')


grok.global_adapter(
    newCollectionWidgetFactory(mode='lines', interface=IWidgetExtractor),
    adapts=(ICollectionSchemaField, Interface, Interface),
    provides=IWidgetExtractor,
    name='lines')


class LinesWidget(SchemaFieldWidget):
    grok.adapts(ICollectionSchemaField, TextLineSchemaField, Interface, Interface)
    grok.name('lines')

    def __init__(self, field, value_field,form, request):
        super(LinesWidget, self).__init__(field, form, request)
        self.text_component = value_field

    def valueToUnicode(self, value):
        return u'\n'.join(value)


class LinesWidgetExtractor(WidgetExtractor):
    grok.adapts(ICollectionSchemaField, TextLineSchemaField, Interface, Interface)
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
