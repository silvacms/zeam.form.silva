# -*- coding: utf-8 -*-
# Copyright (c) 2012 Infrae. All rights reserved.
# See also LICENSE.txt

from zeam.form.base.markers import Marker, NO_VALUE
from zeam.form.ztk.fields import registerSchemaField
from zeam.form.ztk.widgets.textline import TextLineField

from silva.core.conf import schema
from silva.core.interfaces import IVersion, ISilvaObject
from silva.core.interfaces import ISilvaNameChooser, ContentError


class IDField(TextLineField):

    def validate(self, value, form):
        error = super(IDField, self).validate(value, form)
        if error:
            return error
        if not isinstance(value, Marker) and len(value) and form.context:
            context = form.context
            if IVersion.providedBy(context) or ISilvaObject.providedBy(context):
                context = context.get_container()
            try:
                ISilvaNameChooser(context).checkName(value, None)
            except ContentError as error:
                return error.reason
        return None


def IDFieldFactory(schema):
    return IDField(
        schema.title or None,
        identifier=schema.__name__,
        description=schema.description,
        required=schema.required,
        readonly=schema.readonly,
        minLength=schema.min_length,
        maxLength=schema.max_length,
        interface=schema.interface,
        constrainValue=schema.constraint,
        defaultValue=schema.default or NO_VALUE)


def register():
    registerSchemaField(IDFieldFactory, schema.ID)
