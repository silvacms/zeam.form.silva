# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from megrok import pagetemplate as pt

from silva.ui.rest.base import UIREST

from zeam.form.base.form import FormCanvas
from zeam.form.base.markers import SUCCESS
from zeam.form.silva import interfaces
from zeam.form.silva.utils import SilvaFormData
from zeam.form.silva.utils import convert_request_form_to_unicode


REST_ACTIONS_TO_TOKEN = [
    (interfaces.IRESTCloseOnSuccessAction, 'close_on_success'),
    (interfaces.IRESTCloseAction, 'close'),
    (interfaces.IAction, 'send')]


class RESTPopupForm(SilvaFormData, UIREST, FormCanvas):
    grok.baseclass()

    def __init__(self, context, request):
        UIREST.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def renderActions(self):
        def renderAction(action):
            for rest_action, action_type in REST_ACTIONS_TO_TOKEN:
                if rest_action.providedBy(action.component):
                    break
            return {'label': self.translate(action.title),
                    'name': action.identifier,
                    'action': action_type}
        return map(renderAction, self.actionWidgets)

    def processForm(self):
        action, status = self.updateActions()
        self.updateWidgets()
        info = {}
        info['success'] = status == SUCCESS
        if interfaces.IRESTRefreshAction.providedBy(action):
            info['refresh'] = action.refresh
        success_only = interfaces.IRESTSuccessAction.providedBy(action)
        if not (success_only and status == SUCCESS):
            actions = self.renderActions()
            info.update(
                {'label': self.translate(self.label),
                 'widgets': self.render(),
                 'actions': actions,
                 'default_action': actions[0]['name'] if actions else None})
        return self.json_response(info)

    def GET(self):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm()

    def POST(self):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm()


class RESTFormTemplate(pt.PageTemplate):
    pt.view(RESTPopupForm)
