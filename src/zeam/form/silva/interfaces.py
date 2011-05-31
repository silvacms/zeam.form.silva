# -*- coding: utf-8 -*-
# Copyright (c) 2002-2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from zope import interface
from zeam.form.base.interfaces import IFormData, IAction


# Integrate a form in Silva.
class ISilvaFormData(interface.Interface):
    """A form data in Silva.
    """


class ISMIForm(ISilvaFormData, IFormData):
    """A form in SMI.
    """

    def get_content_path(content):
        """Return the relative path of the content.
        """


# Define style for actions
class IRemoverAction(IAction):
    """An action that appear in red.
    """


class ICancelerAction(IAction):
    """An action that cancel something.
    """


class IDefaultAction(IAction):
    """Mark the default action.
    """


# Define categories of actions for RESTForm.
class IRESTAction(IAction):
    """Action design to be used with a RESTForm, that have a special
    meaning.
    """


class IRESTSuccessAction(IRESTAction):
    """Action just send success on success.
    """


class IRESTCloseAction(IRESTAction):
    """Do not call the action callback, just close the RESTForm.
    """


class IRESTCloseOnSuccessAction(IRESTCloseAction, IRESTSuccessAction):
    """Call the action callback, and close the rest Form upon success.
    """


class IRESTRefreshAction(IRESTAction):
    """Trigger the refresh of a form component on the main view.
    """
    refresh = interface.Attribute(u'Identifier to refresh')
