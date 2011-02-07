# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt

from datetime import datetime
from DateTime import DateTime

from ZPublisher.HTTPRequest import FileUpload
from Products.Silva.icon import get_icon_url

from five import grok
from zope.interface import Interface

from silva.core.smi.interfaces import ISMILayer
from silva.core.conf import schema as silvaschema
from silva.translations import translate as _

from zeam.form.base.interfaces import IWidget, IWidgetExtractor
from zeam.form.base.markers import NO_VALUE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField
from zeam.form.ztk.interfaces import ICollectionSchemaField
from zeam.form.ztk.widgets.collection import newCollectionWidgetFactory
from zeam.form.ztk.widgets.date import DatetimeSchemaField
from zeam.form.ztk.widgets.textline import TextLineSchemaField

def register():
    registerSchemaField(FileSchemaField, silvaschema.IBytes)


class FileSchemaField(SchemaField):
    """Field to upload a file.
    """


class FileWidgetInput(SchemaFieldWidget):
    grok.adapts(FileSchemaField, Interface, Interface)
    grok.name('input')

    def valueToUnicode(self, value):
        return u''


class FileWidgetExtractor(WidgetExtractor):
    grok.adapts(FileSchemaField, Interface, Interface)

    def extract(self):
        value = self.request.form.get(self.identifier, u'')
        if not isinstance(value, FileUpload) or not value:
            value = NO_VALUE
        return value, None


class DateTimeFieldWidget(SchemaFieldWidget):
    grok.adapts(DatetimeSchemaField, Interface, ISMILayer)

    def prepareContentValue(self, value):
        if value is NO_VALUE:
            return {self.identifier + '.year': u'',
                    self.identifier + '.month': u'',
                    self.identifier + '.day': u'',
                    self.identifier + '.hour': u'',
                    self.identifier + '.min': u'',
                    self.identifier: u''}
        if isinstance(value, DateTime):
            value = value.asdatetime()
        return {self.identifier + '.year': u'%d' % value.year,
                self.identifier + '.month': u'%02d' % value.month,
                self.identifier + '.day': u'%02d' % value.day,
                self.identifier + '.hour': u'%02d' % value.hour,
                self.identifier + '.min': u'%02d' % value.minute,
                self.identifier: u''}


class DateTimeWidgetExtractor(WidgetExtractor):
    grok.adapts(DatetimeSchemaField, Interface, ISMILayer)

    def extract(self):
        identifier = self.identifier
        value = self.request.form.get(identifier, None)
        if value is None:
            return NO_VALUE, None

        def extract(key, min_value=None, max_value=None, required=True):
            value = self.request.form.get('.'.join((identifier, key)), None)
            if not value:
                if required:
                    raise ValueError(u'Missing %s value' %key)
                return min_value
            try:
                value = int(value)
            except ValueError:
                raise ValueError((u'%s is not a number' % key).capitalize())
            if min_value and max_value:
                if value < min_value or value > max_value:
                    raise ValueError((u'%s is not within %d and %d' % (
                                key, min_value, max_value)).capitalize())
            return value
        try:
            year = extract('year', None, None, self.component.required)
            day = extract('day', 1, 31, year is not None)
            month = extract('month', 1, 12, year is not None)
            hour = extract('hour', 0, 23, False)
            minute = extract('min', 0, 59, False)
        except ValueError, error:
            return (None, _(error))
        if year is None:
            return (NO_VALUE, None)
        try:
            return (datetime(year, month, day, hour, minute), None)
        except ValueError, error:
            return (None, _(str(error).capitalize()))


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
