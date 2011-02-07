# Copyright (c) 2009-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id: addform.py 41849 2010-05-07 12:00:45Z sylvain $

import martian

from zope.component import provideUtility
from zope.component.interfaces import IFactory

from zeam.form.silva.form import SMIAddForm
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
