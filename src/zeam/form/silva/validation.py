# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok

from silva.ui.rest.base import UIREST

from zeam.form.base.interfaces import IFormCanvas
from zeam.form.base.widgets import getWidgetExtractor
from zeam.form.silva.utils import convert_request_form_to_unicode


class RESTValidatorForm(UIREST):
    grok.name('zeam.form.silva.validate')
    grok.context(IFormCanvas)

    def validate(self):
        convert_request_form_to_unicode(self.request.form)
        name = self.request.form['prefix.field']

        info = {'success': True}

        # Look for extractor, extract and validate value.
        for field in self.context.fields:
            extractor = getWidgetExtractor(field, self.context, self.request)
            if extractor is not None:
                if extractor.identifier == name:
                    value, error = extractor.extract()
                    if error is None:
                        error = field.validate(value, self.context.context)
                    if error is not None:
                        info['success'] = False
                        info['error'] = self.translate(error)
                    break
        return self.json_response(info)

    def POST(self):
        return self.validate()


# class RESTRefreshForm(rest.REST):
#     grok.name('zeam.form.silva.refresh')
#     grok.context(SMIComposedForm)

#     def processForm(self, identifier):
#         form = self.context.getSubForm(identifier)
#         if form is None:
#             self.response.setStatus(404)
#             return ''
#         action, status = form.updateActions()
#         form.updateWidgets()
#         return self.json_response(
#             {'form': form.render(),
#              'success': status == SUCCESS})

#     def GET(self, identifier):
#         convert_request_form_to_unicode(self.request.form)
#         return self.processForm(identifier)

#     def POST(self, identifier):
#         convert_request_form_to_unicode(self.request.form)
#         return self.processForm(identifier)
