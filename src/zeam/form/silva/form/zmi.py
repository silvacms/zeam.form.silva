# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from megrok import pagetemplate as pt

from zope.publisher.interfaces.browser import IDefaultBrowserLayer

import js.jqueryui

from zeam.form import base, composed, table
from zeam.form.ztk import validation
from zeam.form.silva.utils import convert_request_form_to_unicode

from silva.fanstatic import need
from silva.core import conf as silvaconf


class IFormResources(IDefaultBrowserLayer):
    silvaconf.resource(js.jqueryui.base)
    silvaconf.resource('zmi.css')
    silvaconf.resource('zmi.js')


class ZopeForm(object):
    """Simple Zope Form.
    """
    grok.baseclass()
    dataValidators = [validation.InvariantsValidation]

    def __init__(self, context, request):
        super(ZopeForm, self).__init__(context, request)
        self.__name__ = self.__view_name__

    def __call__(self):
        need(IFormResources)
        # Request now provide local by default
        assert hasattr(self.request, 'locale')
        convert_request_form_to_unicode(self.request.form)

        return super(ZopeForm, self).__call__()


class ZMIForm(ZopeForm, base.Form):
    """Regular ZMI forms.
    """
    grok.baseclass()
    grok.require('zope2.ViewManagementScreens')


class ZMIFormTemplate(pt.PageTemplate):
    pt.view(ZMIForm)


class ZMIComposedForm(ZopeForm, composed.ComposedForm):
    """ZMI Composed forms.
    """
    grok.baseclass()
    grok.require('zope2.ViewManagementScreens')


class ZMIComposedFormTemplate(pt.PageTemplate):
    pt.view(ZMIComposedForm)


class ZMISubForm(composed.SubForm):
    """ZMI Composed forms.
    """
    grok.baseclass()


class ZMISubFormTemplate(pt.PageTemplate):
    pt.view(ZMISubForm)


class ZMISubTableForm(table.SubTableForm):
    """ZMI table form.
    """
    grok.baseclass()


class ZMISubTableFormTemplate(pt.PageTemplate):
    pt.view(ZMISubTableForm)

