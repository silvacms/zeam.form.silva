
from Acquisition import aq_inner, aq_parent

from silva.core.interfaces import IRoot

from zeam.form.base.actions import Action
from zeam.form.base import SUCCESS



class CancelAddAction(Action):

    def __call__(self, form):
        form.redirect(form.url(name="edit"))
        return SUCCESS


class CancelEditAction(Action):

    def __call__(self, form):
        content = form.context
        if not IRoot.providedBy(content):
            content = aq_parent(aq_inner(content))
        form.redirect(form.url(obj=content, name='edit'))
        return SUCCESS


