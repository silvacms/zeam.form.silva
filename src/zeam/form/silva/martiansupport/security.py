# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five.grok.meta import ViewSecurityGrokker
from zeam.form.silva import form
import martian


class SilvaFormSecurityGrokker(ViewSecurityGrokker):
    """We want to set Zope 2 security on Forms
    """
    martian.component(form.SilvaForm)


class ZopeFormSecurityGrokker(ViewSecurityGrokker):
    """We want to set Zope 2 security on Forms
    """
    martian.component(form.ZopeForm)
