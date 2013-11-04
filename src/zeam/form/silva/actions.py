# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from Acquisition import aq_inner, aq_parent

from five import grok
from zope.interface import Interface

from silva.core.interfaces import IRoot, IZMIObject
from silva.core.interfaces.errors import ContentError
from silva.translations import translate as _

from zope.traversing.browser import absoluteURL
from zeam.form.base import SUCCESS, FAILURE
from zeam.form.base.actions import Action, DecoratedAction
from zeam.form.base.interfaces import IFormData, IAction
from zeam.form.base.widgets import ActionWidget
from zeam.form.ztk.actions import EditAction as BaseEditAction

from .interfaces import ISMIForm, ISilvaFormData, IDisplayWidgetFactory
from .interfaces import IRemoverAction, ICancelerAction, IDefaultAction
from .interfaces import IRESTCloseOnSuccessAction, IRESTCloseAction


class EditAction(BaseEditAction):
    """Edit action
    """
    grok.implements(
        IRESTCloseOnSuccessAction,
        IDefaultAction)
    title = _(u"Save changes")
    description = _(u"Save modifications on the item")
    accesskey = u'ctrl+s'

    def available(self, form):
        return not IDisplayWidgetFactory.providedBy(form.widgetFactory)

    def __call__(self, form):
        try:
            status = super(EditAction, self).__call__(form)
        except (ContentError, ValueError), error:
            if ISilvaFormData.providedBy(form):
                form.send_message(error.args[0], type="error")
            else:
                form.status = error.args[0]
            return FAILURE
        if ISilvaFormData.providedBy(form):
            if status is SUCCESS:
                form.send_message(_(u"Changes saved."), type="feedback")
        return status


class PopupAction(Action):
    """An action that opens a popup form.
    """
    action = None

    def __call__(self, form):
        # It should never be called actually.
        return SUCCESS


class LinkAction(Action):
    """An action that opens as a link in a given target. (Only works in SMI).
    """
    target = '_blank'


class PopupWidget(ActionWidget):
    """Widget to style popup buttons
    """
    grok.adapts(PopupAction, IFormData, Interface)

    def url(self):
        return '/'.join(
            (absoluteURL(self.form.context, self.request),
             '++rest++' + self.component.action))


class SMIActionWidget(ActionWidget):
    grok.adapts(IAction, ISMIForm, Interface)

    def update(self):
        super(SMIActionWidget, self).update()
        self.is_default = IDefaultAction.providedBy(self.component)
        self.css_class = ''
        self.icon = 'ui-icon ui-icon-radio-on'
        if self.is_default:
            self.icon = 'icon form_check'
            self.css_class = 'default-form-control'


class SMILinkActionWidget(SMIActionWidget):
    grok.adapts(LinkAction, ISMIForm, Interface)

    def update(self):
        super(SMILinkActionWidget, self).update()
        self.target = self.component.target


class SMIRemoverWidget(ActionWidget):
    grok.adapts(IRemoverAction, ISMIForm, Interface)


class CancelAction(Action):
    """An action to cancel
    """
    grok.implements(IRESTCloseAction, ICancelerAction)
    title = _(u"Cancel")
    description = _(u"Go back to the previous screen")
    accesskey = u'ctrl+z'
    screen = 'content'

    def getRedirectedContent(self, form):
        return form.context

    def __call__(self, form):
        form.redirect(form.url(obj=self.getRedirectedContent(form)))
        return SUCCESS


class CancelAddAction(CancelAction):
    """Cancel an add action.
    """
    description = _(
        u"Go back to the folder view without adding the item")


class CancelConfigurationAction(CancelAction):
    description = _(u'Go back to the site preferences')
    screen = 'admin'

    def getRedirectedContent(self, form):
        content = form.context
        if IZMIObject.providedBy(content):
            return aq_parent(aq_inner(content))
        return content


class CancelEditAction(CancelAction):
    """Cancel an edit action.
    """
    title = _(u"Back")
    description = _(u"Go back to the folder view")

    def getRedirectedContent(self, form):
        content = form.context
        if not IRoot.providedBy(content):
            content = aq_parent(aq_inner(content))
        return content


class SMICancelWidget(ActionWidget):
    """Widget to style Cancel buttons
    """
    grok.adapts(ICancelerAction, ISMIForm, Interface)

    def update(self):
        super(SMICancelWidget, self).update()
        self.screen = self.component.screen
        self.contentPath = self.form.get_content_path(
            self.component.getRedirectedContent(self.form))


class ExtractedDecoratedAction(DecoratedAction):
    """Action that can be used a factory for the decorator @action,
    which extract data itself before calling the decorated method.
    """

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            return FAILURE
        # We directly give data.
        return super(ExtractedDecoratedAction, self).__call__(form, data)
