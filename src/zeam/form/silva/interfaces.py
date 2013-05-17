# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from zope import interface
from zeam.form.base.interfaces import IFormData, IAction, IWidgetFactory


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


class IDisplayWidgetFactory(IWidgetFactory):
    """Create widgets suitable for display only forms.
    """


class IPublicForm(ISilvaFormData, IFormData):
    """A form for public display.
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
    """Call the action callback, and close the rest form upon success.
    """


class IRESTRefreshAction(IRESTAction):
    """Trigger the refresh of a form component on the main view.
    """
    refresh = interface.Attribute(u'Identifier to refresh')


class IRESTExtraPayloadProvider(interface.Interface):
    """Adapt an action to provides extra payload.
    """

    def get_extra_payload(form):
        """Return the extra payload for the given form.
        """

# This is used by the data manager FieldValueDataManager


class IFieldValueWriter(interface.Interface):
    """Write a field value on a content.
    """

    def __init__(field, form, content):
        """Adapt the given field and content.
        """

    def delete():
        """Remove the value.
        """

    def __call__(value):
        """Save value on the given content.
        """


class IFieldValueReader(interface.Interface):
    """Read a field value from a content.
    """

    def __init__(field, form, content):
        """Adapt the given field and content.
        """

    def __call__():
        """Read the given value.
        """


class IFormLookup(interface.Interface):
    """Return the correct form that match a prefix.
    """

    def fields(self):
        """Return the associated fields.
        """

    def lookup(self, key):
        """Return the associated form.
        """


class IXMLFieldSerializer(interface.Interface):
    identifier = interface.Attribute(u"Field identifier")

    def __call__(producer):
        """Serialize field.
        """


class IXMLFieldDeserializer(interface.Interface):

    def __call__(data, context=None):
        """Deserialize field.
        """


class IXMLFormSerialization(interface.Interface):

    def getSerializer():
        """Return field XML serializer.
        """

    def getDeserializer():
        """Return field XML deserializer.
        """
