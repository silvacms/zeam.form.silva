# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok

from silva.ui.rest.base import UIREST

from zeam.form.base.errors import Error
from zeam.form.base.interfaces import IFormCanvas, ICollection, IError
from zeam.form.base.widgets import getWidgetExtractor
from zeam.form.composed.interfaces import ISubFormGroup
from zeam.form.silva.utils import convert_request_form_to_unicode


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


class RESTValidatorForm(UIREST):
    grok.name('zeam.form.silva.validate')
    grok.context(IFormCanvas)

    def get_form(self, prefix):

        def getter(form):
            if ISubFormGroup.providedBy(form):
                for subform in form.allSubforms:
                    if is_prefix(subform.prefix, prefix):
                        if subform.prefix == prefix:
                            return subform
                        return getter(subform)
            elif form.prefix == prefix:
                return form
            raise KeyError(prefix)

        return getter(self.context)

    def validate(self):
        convert_request_form_to_unicode(self.request.form)
        info = {'success': True}
        fieldname = self.request.form['prefix.field']
        # We need to update the form first, since this is the common
        # place to configure more fields.
        self.context.update()

        try:
            form = self.get_form(self.request.form['prefix.form'])
        except KeyError:
            info['success'] = False
        else:
            # Look for extractor, extract and validate value.
            for field in form.fields:
                extractor = getWidgetExtractor(field, form, self.request)
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

