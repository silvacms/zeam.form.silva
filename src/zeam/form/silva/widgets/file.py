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
from silva.core.interfaces import ISilvaObject
from silva.fanstatic import need
from silva.translations import translate as _

from zeam.form.base.markers import NO_VALUE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField


logger = logging.getLogger('silva.upload')


def register():
    registerSchemaField(FileSchemaField, silvaschema.IBytes)


class FileSchemaField(SchemaField):
    """Field to upload a file.
    """


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
        return absoluteURL(self.form.context, self.request) + '/++rest++zeam.form.silva.upload'

    def displayValue(self):
        value = self.inputValue()
        if value:
            return unicode(os.path.basename(value))
        return _(u'not set, please upload a file.')

    def valueToUnicode(self, value):
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
        if value:
            return open(os.path.join(self.upload_dir(), value), 'r'), None
        return NO_VALUE, None


class Upload(rest.REST):
    """ Check security and return information about gp.fileupload upload
    """
    grok.context(ISilvaObject)
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
