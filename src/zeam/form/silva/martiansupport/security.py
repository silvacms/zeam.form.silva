# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from five.grok.meta import ViewSecurityGrokker
from grokcore.security.components import Permission
from martian.error import GrokError
from zope.component import provideUtility
from zope.security.interfaces import IPermission
import martian

from zeam.form.silva.form.smi import SMIAddForm
from zeam.form.silva.form.public import SilvaForm
from zeam.form.silva.form.zmi import ZopeForm
from zeam.form.silva.form.popup import PopupForm


class SilvaAddFormSecurityGrokker(martian.ClassGrokker):
    """Set the correct permission on add forms.
    """
    martian.component(SMIAddForm)
    martian.directive(grok.name)
    martian.directive(grok.require)
    martian.priority(800)       # Priority > SilvaFormSecurityGrokker

    def execute(self, factory, config, name, require, **kw):
        if not name:
            raise GrokError(u"Add forms must have a name, the meta_type")

        # We define a permission for the add form and use it. For the
        # time being, there is no way to make it optional.

        permission = Permission(
            unicode('silva.add.' + name.replace(' ', '')),
            unicode('Add %ss' % name))

        # Order is set to -1 to be done as soon as possible.
        config.action(
            discriminator=('utility', IPermission, permission.id),
            callable=provideUtility,
            args=(permission, IPermission, permission.id),
            order=-1)

        grok.require.set(factory, [permission.id])
        return True


class PublicFormSecurityGrokker(ViewSecurityGrokker):
    """We want to set Zope 2 security on Forms
    """
    martian.component(SilvaForm)


class ZopeFormSecurityGrokker(ViewSecurityGrokker):
    """We want to set Zope 2 security on Forms
    """
    martian.component(ZopeForm)


class PopupFormSecurityGrokker(ViewSecurityGrokker):
    """We want to set Zope 2 security on Forms
    """
    martian.component(PopupForm)
