# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt

import os.path
import logging
import json

from five import grok
from zope.interface import Interface
from zope.traversing.browser import absoluteURL
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from App.config import getConfiguration

from js.jqueryui import jqueryui

from infrae import rest
from silva.core import conf as silvaconf
from silva.core.conf import schema as silvaschema
from silva.core.interfaces.adapters import IIconResolver
from silva.fanstatic import need
from silva.translations import translate as _

from zeam.form.base.markers import NO_VALUE, NO_CHANGE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField


logger = logging.getLogger('silva.upload')


def register():
    registerSchemaField(FileSchemaField, silvaschema.IBytes)


class FileSchemaField(SchemaField):
    """Field to upload a file.
    """
    fileSetLabel = _('Current file.')
    fileNotSetLabel = _(u'Not set, please upload a file.')


class IUploadResources(IDefaultBrowserLayer):
    silvaconf.resource(jqueryui)
    silvaconf.resource('upload.js')


class FileWidgetInput(SchemaFieldWidget):
    grok.adapts(FileSchemaField, Interface, Interface)
    grok.name('input')

    def update(self):
        need(IUploadResources)
        super(FileWidgetInput, self).update()

    def uploadURL(self):
        return absoluteURL(self.form.context, self.request) + \
            '/++rest++zeam.form.silva.upload'

    def prepareContentValue(self, value):
        formatted_value = u''
        if value is not NO_VALUE:
            formatted_value = self.valueToUnicode(NO_CHANGE)
        return {self.identifier: formatted_value}

    def displayValue(self):
        value = self.inputValue()
        label = None
        if value:
            if value != u'__NO_CHANGE__':
                return {'icon': None,
                        'message': None,
                        'filename': unicode(os.path.basename(value))}
            label = self.component.fileSetLabel
        else:
            label = self.component.fileNotSetLabel
        icon = IIconResolver(self.request).get_tag(None)
        return {'icon': icon, 'message': label, 'filename': None}

    def valueToUnicode(self, value):
        if value is NO_CHANGE:
            return u'__NO_CHANGE__'
        return unicode(value)


class FileWidgetExtractor(WidgetExtractor):
    grok.adapts(FileSchemaField, Interface, Interface)

    @classmethod
    def upload_dir(cls):
        if hasattr(cls, '_upload_dir_cache'):
            return cls._upload_dir_cache
        zconf = getattr(getConfiguration(), 'product_config', {})
        config = zconf.get('zeam.form.silva', {})
        upload_dir = config.get('upload-directory', None)
        if upload_dir is None:
            raise RuntimeError(
                '(zeam.form.silva) upload directory no configured')
        cls._upload_dir_cache = upload_dir
        return upload_dir

    def extract(self):
        value = self.request.form.get(self.identifier, u'')
        if value == "__NO_CHANGE__":
            return NO_CHANGE, None
        if value:
            return open(os.path.join(self.upload_dir(), value), 'r'), None
        return NO_VALUE, None


class Upload(rest.REST):
    """ Check security and return information about gp.fileupload upload
    """
    grok.context(Interface)
    grok.require('silva.ChangeSilvaContent')
    grok.name('zeam.form.silva.upload')

    def POST(self):
        """ get information about file upload
        """
        upload_id = long(self.request.get('gp.fileupload.id'))
        paths = self.request.environ.get('HTTP_STORED_PATHS', '').split(':')
        path = paths[0]
        logger.info("upload paths: %r" % paths)
        return """
            <html>
                <body>
                    <script>
                        var $ = window.parent.jQuery;
                        $(window.parent.document).trigger('done-%d-upload', %s);
                    </script>
                </body>
            </html>
        """ % (upload_id, json.dumps({'path': path, 'upload-id': upload_id}))
