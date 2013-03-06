# -*- coding: utf-8 -*-
# Copyright (c) 2012-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import logging

from zeam import component
from zeam.form.base.interfaces import IFormData
from zeam.form.silva.interfaces import IXMLFormSerialization
from zeam.form.silva.interfaces import IXMLFieldSerializer
from zeam.form.silva.interfaces import IXMLFieldDeserializer
from Products.Formulator.Errors import ValidationError
from Products.Formulator.zeamsupport import IFormulatorField

logger = logging.getLogger('silva.core.xml')


class FieldSerializer(component.Component):
    """Make possible to serialize a field in XML.
    """
    component.adapts(IFormulatorField, IFormData)
    component.provides(IXMLFieldSerializer)

    def __init__(self, field, form, value):
        self.identifier = field.identifier
        self.field = field._field
        self.form = form
        self.value = value

    def serialize(self, producer):
        if self.value is not None:
            self.field.validator.serializeValue(
                self.field, self.value, producer)

    def __call__(self, producer):
        self.serialize(producer)


class FieldDeserializer(component.Component):
    """Make possible to deserialize a field in XML.
    """
    component.adapts(IFormulatorField, IFormData)
    component.provides(IXMLFieldDeserializer)

    def __init__(self, field, form):
        self.identifier = field.identifier
        self.field = field._field
        self.form = form

    def deserialize(self, data, context=None):
        try:
            return self.field.validator.deserializeValue(
                self.field, data, context=context)
        except ValidationError as error:
            logger.error(
                u'Cannot set Formulator field value %s: %s',
                self.field.getId(), str(error.error_text))

    def write(self, value):
        self.form.getContentData().set(self.identifier, value)

    def __call__(self, data, context=None):
        self.write(self.deserialize(data, context=context))


class XMLFormSerialization(component.Component):
    component.adapts(IFormData)
    component.provides(IXMLFormSerialization)

    def __init__(self, form):
        self.form = form

    def getSerializers(self):
        form = self.form
        assert form.getContent() is not None
        content = form.getContentData()
        for field in form.fields:
            try:
                value = content.get(field.identifier)
            except KeyError:
                continue
            factory = component.getComponent(
                (field, form), IXMLFieldSerializer)
            yield factory(field, form, value)

    def getDeserializers(self):
        form = self.form
        deserializers = {}
        for field in form.fields:
            deserializers[field.identifier] = component.getWrapper(
                (field, form), IXMLFieldDeserializer)
        return deserializers
