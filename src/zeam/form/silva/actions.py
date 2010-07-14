
from Acquisition import aq_inner, aq_parent

from five import grok
from zope.interface import Interface
from silva.core.interfaces import IRoot

from zeam.form.base import SUCCESS
from zeam.form.base.actions import Action
from zeam.form.base.interfaces import IFormData
from zeam.form.base.widgets import ActionWidget


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
    grok.adapts(CancelAction, IFormData, Interface)

    def htmlClass(self):
        return 'canceler'
