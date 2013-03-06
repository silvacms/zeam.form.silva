# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import Interface
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from js.jquery import jquery

from silva.core import conf as silvaconf
from silva.core.conf import schema as silvaschema
from silva.fanstatic import need

from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField


class CropSchemaField(SchemaField):
    """ Field to set cropping of image
    """


class ICropResources(IDefaultBrowserLayer):
    silvaconf.resource(jquery)
    silvaconf.resource('jquery.Jcrop.js')
    silvaconf.resource('jquery.Jcrop.css')
    silvaconf.resource('cropping.js')


class CropImageInputWidget(SchemaFieldWidget):
    grok.adapts(CropSchemaField, Interface, Interface)
    grok.name(u'input')

    def update(self):
        super(CropImageInputWidget, self).update()
        need(ICropResources)
        self.url = self.form.url(self.form.context) + '?hires'

    def valueToUnicode(self, value):
        return unicode(value)


def register():
    registerSchemaField(CropSchemaField, silvaschema.ICropCoordinates)


