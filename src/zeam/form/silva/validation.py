# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok

from silva.ui.rest.base import UIREST

from zeam.form.base.interfaces import IFormCanvas
from zeam.form.composed.interfaces import ISubFormGroup
from zeam.form.base.widgets import getWidgetExtractor
from zeam.form.silva.utils import convert_request_form_to_unicode


def is_prefix(prefix, value):
    return (value.startswith(prefix) and
            (len(value) == len(prefix) or
             value[len(prefix)] == '.'))


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
                            info['success'] = False
                            info['error'] = self.translate(error)
                        break
            else:
                info['success'] = False
        return self.json_response(info)

    def POST(self):
        return self.validate()

