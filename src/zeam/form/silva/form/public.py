# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zExceptions import Redirect

from five import grok
from zope import component
from zope.publisher.publish import mapply

from zeam.form import base, viewlet
from zeam.form.silva.utils import SilvaFormData
from zeam.form.silva.utils import convert_request_form_to_unicode
from zeam.form.ztk import validation

from grokcore.layout.interfaces import IPage, ILayout
from silva.core.layout.interfaces import ISilvaLayer
from silva.core.views.views import HTTPHeaderView



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
        self.setHTTPHeaders()
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

