# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from zExceptions import Redirect

from five import grok
from megrok import pagetemplate as pt
from grokcore.layout.interfaces import IPage, ILayout

from zope import component
from zope.interface import Interface
from zope.publisher.publish import mapply
from zope.publisher.interfaces.browser import IDefaultBrowserLayer

from zeam.form import base, viewlet
from zeam.form.silva.utils import SilvaFormData
from zeam.form.silva.utils import convert_request_form_to_unicode
from zeam.form.silva.interfaces import IPublicForm, ICancelerAction
from zeam.form.ztk import validation
from zeam.form.base.widgets import ActionWidget
from zeam.form.base.interfaces import IAction

from silva.core import conf as silvaconf
from silva.core.layout.interfaces import ISilvaLayer
from silva.core.views.views import HTTPHeaderView


class IPublicFormResources(IDefaultBrowserLayer):
    """Resources for Silva forms.
    """
    silvaconf.resource('public.css')


class SilvaForm(HTTPHeaderView, SilvaFormData):
    """Form in Silva.
    """
    grok.baseclass()
    grok.implements(IPage)
    dataValidators = [validation.InvariantsValidation]

    def __init__(self, context, request):
        super(SilvaForm, self).__init__(context, request)
        self.__name__ = self.__view_name__
        self.layout = None

    def default_namespace(self):
        namespace = super(SilvaForm, self).default_namespace()
        namespace['layout'] = self.layout
        return namespace

    def content(self):
        return self.render()

    def __call__(self):
        convert_request_form_to_unicode(self.request.form)

        self.layout = component.getMultiAdapter(
            (self.request, self.context), ILayout)

        mapply(self.update, (), self.request)
        if self.request.response.getStatus() in (302, 303):
            # A redirect was triggered somewhere in update(). Don't
            # continue processing the form
            return

        self.updateForm()
        if self.request.response.getStatus() in (302, 303):
            return

        return self.layout(self)


class PublicForm(SilvaForm, base.Form):
    """Regular SMI form.
    """
    grok.baseclass()
    grok.layer(ISilvaLayer)
    grok.require('zope.Public')
    grok.implements(IPublicForm)


class PublicFormTemplate(pt.PageTemplate):
    pt.view(PublicForm)


class PublicActionWidget(ActionWidget):
    grok.adapts(IAction, IPublicForm, Interface)

    ## ovverride ActionWidget function
    def htmlClass(self):
        if ICancelerAction.providedBy(self.component):
            return 'action cancel'
        return 'action submit'


class PublicViewletForm(SilvaFormData, viewlet.ViewletForm):
    """ Base form in viewlet
    """
    grok.baseclass()

    def available(self):
        for action in self.actions:
            if action.available(self):
                return True
        return False

    def update(self):
        convert_request_form_to_unicode(self.request.form)
        return super(PublicViewletForm, self).update()

    def redirect(self, url):
        # Raise redirect exception to be not to render the current
        # page anymore.
        raise Redirect(url)


class PublicContentProviderForm(SilvaFormData, viewlet.ViewletManagerForm):
    grok.baseclass()

    def update(self):
        convert_request_form_to_unicode(self.request.form)
        return super(PublicContentProviderForm, self).update()

    def redirect(self, url):
        # Raise redirect exception to be not to render the current
        # page anymore.
        raise Redirect(url)
