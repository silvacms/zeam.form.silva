# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import logging
import json

from five import grok
from zope.interface import Interface
from zope.traversing.browser import absoluteURL
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from js.jqueryui import jqueryui

from infrae import rest
from silva.core import conf as silvaconf
from silva.core import interfaces
from silva.core.conf import schema as silvaschema
from silva.core.interfaces.adapters import IIconResolver
from silva.fanstatic import need
from silva.translations import translate as _

from zeam.form.base.errors import Error
from zeam.form.base.markers import NO_VALUE, NO_CHANGE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.composed.interfaces import ISubForm
from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField
from zeam.form.silva.interfaces import ISMIForm

logger = logging.getLogger('silva.upload')


def register():
    registerSchemaField(FileSchemaField, silvaschema.IBytes)


class FileSchemaField(SchemaField):
    """Field to upload a file.
    """
    fileSetLabel = _('Current file.')
    fileNotSetLabel = _(u'Not set, please upload a file.')


class BasicFileWidgetInput(SchemaFieldWidget):
    grok.adapts(FileSchemaField, Interface, Interface)
    grok.name('input')

    def prepareContentValue(self, value):
        formatted_value = u''
        if value is not NO_VALUE:
            formatted_value = self.valueToUnicode(NO_CHANGE)
        return {self.identifier: formatted_value}

    def prepareRequestValue(self, value, extractor):
        formatted_value = u''
        if (value.get(self.identifier + '.change') in ['change', 'keep'] or
            bool(value.get(self.identifier))):
            formatted_value = self.valueToUnicode(NO_CHANGE)
        return {self.identifier: formatted_value}

    def valueStatus(self):
        value = self.inputValue()
        if value == u'__NO_CHANGE__':
            return True
        return False

    def valueToUnicode(self, value):
        if value is NO_CHANGE:
            return u'__NO_CHANGE__'
        return unicode(value)


class BasicFileWidgetExtractor(WidgetExtractor):
    grok.adapts(FileSchemaField, Interface, Interface)

    def extract(self):
        operation = self.request.form.get(self.identifier + '.change')
        if operation == "keep":
            return NO_CHANGE, None
        if operation == "erase":
            return NO_VALUE, None
        if operation == "change":
            value = self.request.form.get(self.identifier)
            if value:
                return value, None
            return None, Error("Missing file", identifier=self.identifier)
        value = self.request.form.get(self.identifier)
        if value:
            return value, None
        return NO_VALUE, None


class IUploadResources(IDefaultBrowserLayer):
    silvaconf.resource(jqueryui)
    silvaconf.resource('upload.js')


class FileWidgetInput(SchemaFieldWidget):
    grok.adapts(FileSchemaField, ISMIForm, Interface)
    grok.name('input')

    def update(self):
        need(IUploadResources)
        super(FileWidgetInput, self).update()

    def uploadIdentifier(self):
        manager = self.request.environ.get('infrae.fileupload.manager')
        if manager is None:
            raise interfaces.Error('The upload component is not available')
        return manager.create_identifier()

    def uploadURL(self):
        manager = self.request.environ.get('infrae.fileupload.manager')
        if manager is None:
            raise interfaces.Error('The upload component is not available')
        if manager.upload_url:
            return manager.upload_url
        if ISubForm.providedBy(self.form):
            form = self.form.getComposedForm()
        else:
            form = self.form
        return absoluteURL(form, self.request) + \
            '/upload'

    def prepareContentValue(self, value):
        formatted_value = u''
        if value is not NO_VALUE:
            formatted_value = self.valueToUnicode(NO_CHANGE)
        return {self.identifier: formatted_value}

    def displayValue(self):
        value = self.inputValue()
        status = None
        label = None
        icon = IIconResolver(self.request).get_tag(None)
        if value:
            label = self.component.fileSetLabel
            if value != u'__NO_CHANGE__':
                manager = self.request.environ.get('infrae.fileupload.manager')
                if manager is None:
                    raise interfaces.Error(
                        'The upload component is not available.')
                bucket = manager.access_upload_bucket(value)
                if bucket is not None:
                    status = json.dumps(bucket.get_status())
        else:
            label = self.component.fileNotSetLabel
        return {'icon': icon,
                'message': label,
                'status': status,
                'empty': status is None}

    def valueToUnicode(self, value):
        if value is NO_CHANGE:
            return u'__NO_CHANGE__'
        return unicode(value)


class UploadedFile(object):

    def __init__(self, bucket):
        metadata = bucket.get_status()
        self.name = metadata.get('filename') # Python filename
        self.filename = metadata.get('filename') # Zope filename
        self.__descriptor = open(bucket.get_filename(), 'r')

    def __getattr__(self, name):
        return getattr(self.__descriptor, name)


class FileWidgetExtractor(WidgetExtractor):
    grok.adapts(FileSchemaField, ISMIForm, Interface)

    def extract(self):
        value = self.request.form.get(self.identifier, u'')
        if value == "__NO_CHANGE__":
            return NO_CHANGE, None
        if not value:
            return NO_VALUE, None
        manager = self.request.environ.get('infrae.fileupload.manager')
        if manager is None:
            raise interfaces.Error('The upload component is not available')
        bucket = manager.access_upload_bucket(value)
        if bucket is not None:
            if not bucket.is_complete():
                return NO_VALUE, _(u"Upload is incomplete.")
            return UploadedFile(bucket), None
        return NO_VALUE, _(u"Upload failed.")


class Upload(rest.REST):
    """ Check security and return information about gp.fileupload upload
    """
    grok.adapts(ISMIForm, Interface)
    grok.require('silva.ChangeSilvaContent')
    grok.name('upload')

    def POST(self):
        """ get information about file upload
        """
        info = self.request.environ['infrae.fileupload.current'].get_status()
        return """
            <html>
                <body data-upload-identifier="%s" data-upload-info="%s">
                </body>
            </html>
        """ % (str(info['identifier']), json.dumps(info).replace('"', '\\"'))
