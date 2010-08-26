# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from megrok import pagetemplate as pt
from infrae import rest

from zeam.form.base.form import FormCanvas
from zeam.form.silva.form import SilvaFormData
from zeam.form.silva.utils import convert_request_form_to_unicode


class RESTForm(SilvaFormData, rest.REST, FormCanvas):
    grok.baseclass()

    # Post form are not supported
    postOnly = False

    def __init__(self, context, request):
        # XXX I loved super
        rest.REST.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def renderActions(self):
        def renderAction(action):
            return {'label': action.title,
                    'name': action.identifier}
        return map(renderAction, self.actionWidgets)

    def processForm(self):
        self.updateActions()
        self.updateWidgets()
        return self.json_response(
            {'label': self.label,
             'widgets': self.render(),
             'actions': self.renderActions()})

    def GET(self):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm()

    def POST(self):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm()

    def PUT(self):
        convert_request_form_to_unicode(self.request.form)
        self.updateActions()


class RESTFormTemplate(pt.PageTemplate):
    pt.view(RESTForm)
