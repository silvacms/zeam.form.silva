# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from five.grok.meta import ViewSecurityGrokker, GrokError
from grokcore.security.components import Permission
from zeam.form.silva import form
from zope.component import provideUtility
from zope.security.interfaces import IPermission
import martian


class SilvaAddFormSecurityGrokker(martian.ClassGrokker):
    """Set the correct permission on add forms.
    """
    martian.component(form.SMIAddForm)
    martian.directive(grok.name)
    martian.directive(grok.require)
    martian.priority(800)       # Priority > SilvaFormSecurityGrokker

    def execute(self, factory, config, name, require, **kw):
        if not name:
            raise GrokError(u"Add forms must have a name, the meta_type")

        if grok.require.dotted_name() not in factory.__dict__:
            # The grok.require permission have not been used. We
            # define a permission for the add form and use it.

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
        return False


class SilvaFormSecurityGrokker(ViewSecurityGrokker):
    """We want to set Zope 2 security on Forms
    """
    martian.component(form.SilvaForm)
    martian.priority(400)


class ZopeFormSecurityGrokker(ViewSecurityGrokker):
    """We want to set Zope 2 security on Forms
    """
    martian.component(form.ZopeForm)
