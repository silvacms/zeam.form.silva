from zope.configuration.name import resolve

from silva.core.interfaces import IRoot
from silva.core.conf.utils import getFactoryName

from zeam.form.silva.interfaces import IDefaultAddFields
from zeam.form.base.actions import Action
from zeam.form.base import FAILURE

from Products.Silva.ExtensionRegistry import extensionRegistry


class CancelAddAction(Action):
    def __call__(self, form):
        return form.redirect(form.url(name="edit"))


class CancelEditAction(Action):

    def __call__(self, form):
        content = form.context
        if not IRoot.providedBy(form.context):
            content = form.context.aq_inner.aq_parent
        return form.redirect(form.url(obj=content, name='edit'))


