# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Acquisition import aq_inner, aq_parent

from five import grok
from zope.interface import Interface

from silva.core.interfaces import IRoot
from silva.translations import translate as _

from zeam.form.base import SUCCESS, FAILURE
from zeam.form.base.actions import Action, DecoratedAction
from zeam.form.base.interfaces import IFormData
from zeam.form.base.widgets import ActionWidget

from zeam.form.silva.interfaces import ISilvaFormData


class CancelAction(Action):
    """A action to cancel
    """


class CancelAddAction(CancelAction):
    """Cancel an add action.
    """

    def __call__(self, form):
        form.redirect(form.url(name="edit"))
        return SUCCESS


class CancelEditAction(CancelAction):
    """Cancel an edit action.
    """

    def __call__(self, form):
        content = form.context
        if not IRoot.providedBy(content):
            content = aq_parent(aq_inner(content))
        form.redirect(form.url(obj=content, name='edit'))
        return SUCCESS


class CancelWidget(ActionWidget):
    """Widget to style Cancel buttons
    """
    grok.adapts(CancelAction, IFormData, Interface)

    def htmlClass(self):
        return 'canceler'


class ExtractedDecoratedAction(DecoratedAction):
    """Action that can be used a factory for the decorator @action,
    which extract data itself before calling the decorated method.
    """

    def __call__(self, form):
        data, errors = form.extractData()
        if errors:
            assert ISilvaFormData.providedBy(form)
            form.send_message(_(u"There were errors."), type=u"error")
            return FAILURE
        # We directly give data.
        return super(ExtractedDecoratedAction, self).__call__(form, data)
