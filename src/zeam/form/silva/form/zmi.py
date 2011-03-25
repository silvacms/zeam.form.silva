# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from megrok import pagetemplate as pt

from zope.cachedescriptors.property import CachedProperty
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

import js.jqueryui

from zeam.form import base, composed
from zeam.form.ztk import validation
from zeam.form.silva.utils import find_locale, convert_request_form_to_unicode

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

    @CachedProperty
    def i18nLanguage(self):
        adapter = IUserPreferredLanguages(self.request)
        languages = adapter.getPreferredLanguages()
        if languages:
            return languages[0]
        return 'en'

    def __init__(self, context, request):
        super(ZopeForm, self).__init__(context, request)
        self.__name__ = self.__view_name__

    def __call__(self):
        need(IFormResources)
        if not hasattr(self.request, 'locale'):
            # This is not pretty, but no choice.
            self.request.locale = find_locale(self.request)
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


