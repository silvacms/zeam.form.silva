# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from __future__ import absolute_import

from datetime import datetime
from datetime import date
from DateTime import DateTime

from five import grok
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from js.jqueryui import jqueryui

from silva.core import conf as silvaconf
from silva.translations import translate as _
from silva.fanstatic import need

from zeam.form.base.markers import NO_VALUE
from zeam.form.base.widgets import WidgetExtractor, FieldWidget
from zeam.form.ztk.widgets.date import DatetimeField
from zeam.form.ztk.widgets.date import DateField


class IDateTimeResources(IDefaultBrowserLayer):
    silvaconf.resource(jqueryui)
    silvaconf.resource('datetime.js')


class DateTimeFieldWidget(FieldWidget):
    grok.adapts(DatetimeField, Interface, Interface)
    defaultHtmlClass = ['field', 'field-datetime']

    displayTime = True

    def update(self):
        need(IDateTimeResources)
        super(DateTimeFieldWidget, self).update()

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
    grok.adapts(DatetimeField, Interface, Interface)

    def extract(self):
        identifier = self.identifier
        value = self.request.form.get(identifier, None)
        if value is None:
            return NO_VALUE, None

        def extract(key, min_value=None, max_value=None, required=True):
            value = self.request.form.get('.'.join((identifier, key)), None)
            if not value:
                if required:
                    raise ValueError(u'Missing %s value.' %key)
                return min_value
            try:
                value = int(value)
            except ValueError:
                raise ValueError((u'%s is not a number.' % key).capitalize())
            if min_value and max_value:
                if value < min_value or value > max_value:
                    raise ValueError((u'%s is not within %d and %d.' % (
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


class DateFieldWidget(DateTimeFieldWidget):
    grok.adapts(DateField, Interface, Interface)
    defaultHtmlClass = ['field', 'field-date']

    displayTime = False

    def prepareContentValue(self, value):
        if value is NO_VALUE:
            return {self.identifier + '.year': u'',
                    self.identifier + '.month': u'',
                    self.identifier + '.day': u'',
                    self.identifier: u''}
        return {self.identifier + '.year': u'%d' % value.year,
                self.identifier + '.month': u'%02d' % value.month,
                self.identifier + '.day': u'%02d' % value.day,
                self.identifier: u''}


class DateWidgetExtractor(DateTimeWidgetExtractor):
    grok.adapts(DateField, Interface, Interface)

    def extract(self):
        value, error = super(DateWidgetExtractor, self).extract()
        if error is None:
            return date(value.year, value.month, value.day), None
        return value, error
