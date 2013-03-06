# -*- coding: utf-8 -*-
# Copyright (c) 2009-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import martian

from zope.component import provideUtility
from zope.component.interfaces import IFactory

from zeam.form.silva.form.smi import SMIAddForm
from silva.core import conf as silvaconf


class AddFormGrokker(martian.ClassGrokker):
    """ Grok add form and register them as factories.
    """
    martian.component(SMIAddForm)
    martian.directive(silvaconf.name)

    def execute(self, form, name, config, **kw):
        config.action(
            discriminator = ('utility', IFactory, name),
            callable = provideUtility,
            args = (form, IFactory, name))
        return True
