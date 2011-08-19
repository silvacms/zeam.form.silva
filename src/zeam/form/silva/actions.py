# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Acquisition import aq_inner, aq_parent

from five import grok
from zope.interface import Interface

from silva.core.interfaces import IRoot
from silva.translations import translate as _

from zope.traversing.browser import absoluteURL
from zeam.form.base import SUCCESS, FAILURE
from zeam.form.base.actions import Action, DecoratedAction
from zeam.form.base.interfaces import IFormData, IAction
from zeam.form.base.widgets import ActionWidget
from zeam.form.base.markers import getValue, DISPLAY
from zeam.form.ztk.actions import EditAction as BaseEditAction

from zeam.form.silva import interfaces


class EditAction(BaseEditAction):
    """Edit action
    """
    grok.implements(
        interfaces.IRESTCloseOnSuccessAction, interfaces.IDefaultAction)
    title = _(u"Save changes")
    description = _(u"save modifications")
    accesskey = u'ctrl+s'

    def available(self, form):
        for field in form.fields:
            if getValue(field, 'mode', form) != DISPLAY:
                return True
        return False

    def __call__(self, form):
        try:
            status = super(EditAction, self).__call__(form)
        except ValueError, error:
            form.send_message(error.args[0], type="error")
            return FAILURE
        if interfaces.ISilvaFormData.providedBy(form):
            if status is FAILURE:
                for error in form.formErrors:
                    form.send_message(error.title, type="error")
            else:
                form.send_message(_(u"Changes saved."), type="feedback")
        return status


class PopupAction(Action):
    """An action that opens a popup form.
    """
    action = None

    def __call__(self, form):
        # It should never be called actually.
        return SUCCESS


class PopupWidget(ActionWidget):
    """Widget to style popup buttons
    """
    grok.adapts(PopupAction, IFormData, Interface)

    def url(self):
        return '/'.join(
            (absoluteURL(self.form.context, self.request),
             '++rest++' + self.component.action))


class SMIActionWidget(ActionWidget):
    grok.adapts(IAction, interfaces.ISMIForm, Interface)

    def update(self):
        super(SMIActionWidget, self).update()
        self.is_default = interfaces.IDefaultAction.providedBy(self.component)
        self.css_class = 'form-control'
        if self.is_default:
            self.css_class += ' default-form-control'


class SMIRemoverWidget(ActionWidget):
    grok.adapts(interfaces.IRemoverAction, interfaces.ISMIForm, Interface)


class CancelAction(Action):
    """A action to cancel
    """
    grok.implements(interfaces.IRESTCloseAction, interfaces.ICancelerAction)
    title = _(u"Cancel")
    description = _(u"go back to the folder view")
    accesskey = u'ctrl+z'

    def getRedirectedContent(self, form):
        return form.context

    def __call__(self, form):
        form.redirect(form.url(obj=self.getRedirectedContent(form)))
        return SUCCESS


class CancelAddAction(CancelAction):
    """Cancel an add action.
    """
    description = _(
        u"go back to the folder view without adding the content")



class CancelEditAction(CancelAction):
    """Cancel an edit action.
    """
    description = _(
        u"go back to the folder view without editing the content")

    def getRedirectedContent(self, form):
        content = form.context
        if not IRoot.providedBy(content):
            content = aq_parent(aq_inner(content))
        return content


class SMICancelWidget(ActionWidget):
    """Widget to style Cancel buttons
    """
    grok.adapts(interfaces.ICancelerAction, interfaces.ISMIForm, Interface)

    def update(self):
        super(SMICancelWidget, self).update()
        self.screen = 'content'
        self.contentPath = self.form.get_content_path(
            self.component.getRedirectedContent(self.form))



class ExtractedDecoratedAction(DecoratedAction):
    """Action that can be used a factory for the decorator @action,
    which extract data itself before calling the decorated method.
    """

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            if interfaces.ISilvaFormData.providedBy(form):
                for error in form.formErrors:
                    form.send_message(error.title, type="error")
            return FAILURE
        # We directly give data.
        return super(ExtractedDecoratedAction, self).__call__(form, data)
