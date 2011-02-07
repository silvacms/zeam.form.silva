# Copyright (c) 2010-2011 Infrae. All rights reserved.
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
from zeam.form.base.interfaces import IFormData
from zeam.form.base.widgets import ActionWidget
from zeam.form.ztk.actions import EditAction as BaseEditAction

from zeam.form.silva import interfaces


class EditAction(BaseEditAction):
    """Edit action
    """
    grok.implements(interfaces.IRESTCloseOnSuccessAction)
    title = _(u"save changes")
    description = _(u"save modifications: alt-s")
    accesskey = u's'

    def __call__(self, form):
        status = super(EditAction, self).__call__(form)
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


class RemoverWidget(ActionWidget):
    """Widget in red.
    """
    grok.adapts(interfaces.IRemoverAction, IFormData, Interface)

    def htmlClass(self):
        return 'action remover'


class CancelAction(Action):
    """A action to cancel
    """
    grok.implements(interfaces.IRESTCloseAction, interfaces.ICancelerAction)
    title = _(u"cancel")
    description = _(u"go back to the folder view: alt-c")
    accesskey = u'c'

    def __call__(self, form):
        form.redirect(form.url(name="edit"))
        return SUCCESS


class CancelAddAction(CancelAction):
    """Cancel an add action.
    """
    description = _(
        u"go back to the folder view without adding the content: alt-c")

    def __call__(self, form):
        form.redirect(form.url(name="edit"))
        return SUCCESS


class CancelEditAction(CancelAction):
    """Cancel an edit action.
    """
    description = _(
        u"go back to the folder view without editing the content: alt-c")

    def __call__(self, form):
        content = form.context
        if not IRoot.providedBy(content):
            content = aq_parent(aq_inner(content))
        form.redirect(form.url(obj=content, name='edit'))
        return SUCCESS


class CancelWidget(ActionWidget):
    """Widget to style Cancel buttons
    """
    grok.adapts(interfaces.ICancelerAction, IFormData, Interface)

    def htmlClass(self):
        return 'canceler'


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
