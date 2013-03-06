# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.interface import Interface

from silva.ui.rest.base import UIREST

from zeam.form.base.errors import Error
from zeam.form.base.interfaces import IFormCanvas, ICollection, IError
from zeam.form.composed.interfaces import ISubFormGroup
from zeam.form.silva.utils import convert_request_form_to_unicode
from zeam.form.silva.interfaces import IFormLookup


def is_prefix(prefix, value):
    return (value.startswith(prefix) and
            (len(value) == len(prefix) or
             value[len(prefix)] == '.'))


def serialize_error(rest, errors):
    result = {errors.identifier: rest.translate(errors.title)}
    if ICollection.providedBy(errors):
        for error in errors:
            result.update(serialize_error(rest, error))
    return result


class DefaultFormLookup(grok.Adapter):
    grok.context(Interface)
    grok.provides(IFormLookup)
    grok.implements(IFormLookup)

    def __init__(self, form):
        self.form = form

    def fields(self):
        return self.form.fields

    def lookup(self, key):
        if self.form.prefix == key:
            return self
        raise KeyError(key)


class SubFormLookup(DefaultFormLookup):
    grok.context(ISubFormGroup)

    def lookup(self, key):
        for subform in self.form.allSubforms:
            if is_prefix(subform.prefix, key):
                subfetcher = IFormLookup(subform)
                if subform.prefix == key:
                    return subfetcher
                return subfetcher.lookup(key)
        return super(SubFormLookup, self).lookup(key)


class RESTValidatorForm(UIREST):
    grok.name('zeam.form.silva.validate')
    grok.context(IFormCanvas)

    def validate(self):
        convert_request_form_to_unicode(self.request.form)
        info = {'success': True}
        fieldname = self.request.form['prefix.field']
        # We need to update the form first, since this is the common
        # place to configure more fields.
        self.context.update()

        try:
            lookup = IFormLookup(self.context).lookup(
                self.request.form['prefix.form'])
        except KeyError:
            info['success'] = False
        else:
            # Look for extractor, extract and validate value.
            for field in lookup.fields():
                extractor = lookup.form.widgetFactory.extractor(field)
                if extractor is not None:
                    if extractor.identifier == fieldname:
                        value, error = extractor.extract()
                        if error is None:
                            error = field.validate(value, self.context)
                        if error is not None:
                            if not IError.providedBy(error):
                                error = Error(title=error, identifier=fieldname)
                            info['success'] = False
                            info['errors'] = serialize_error(self, error)
                        break
            else:
                info['success'] = False
        return self.json_response(info)

    def POST(self):
        return self.validate()

