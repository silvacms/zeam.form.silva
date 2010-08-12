# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import schema
from zope.interface import Interface

from silva.core.conf import schema as silvaschema
from silva.translations import translate as _


# Silva forms

class ISilvaFormData(Interface):
    """A form data in Silva.
    """


class IDefaultAddFields(Interface):
    """Default fields used in a add form. You don't have to defines
    this fields.
    """

    id = silvaschema.ID(
        title=_(u"id"),
        description=_(u"No spaces or special characters besides ‘_’ or ‘-’ or ‘.’"),
        required=True)
    title = schema.TextLine(
        title=_(u"title"),
        description=_(u"The title will be publicly visible, and is used for the link in indexes."),
        required=True)
