# -*- coding: utf-8 -*-
# Copyright (c) 2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

import json
from operator import itemgetter

from five import grok
from megrok import pagetemplate as pt

from silva.ui.rest.base import UIREST, UIHelper
from silva.ui.rest.base import get_resources

from zeam.form.base.form import FormCanvas, Form
from zeam.form.base.markers import SUCCESS, FAILURE
from zeam.form.silva import interfaces
from zeam.form.silva.utils import SilvaFormData
from zeam.form.silva.utils import convert_request_form_to_unicode


REST_ACTIONS_TO_TOKEN = [
    (interfaces.IRESTCloseOnSuccessAction, 'close_on_success'),
    (interfaces.IRESTCloseAction, 'close'),
    (interfaces.IAction, 'send')]


class PopupCanvas(SilvaFormData, FormCanvas, UIHelper):
    grok.baseclass()

    def update(self):
        pass

    def renderActions(self):

        def renderAction(action):
            for rest_action, action_type in REST_ACTIONS_TO_TOKEN:
                if rest_action.providedBy(action.component):
                    break
            return {'label': self.translate(action.title),
                    'name': action.identifier,
                    'action': action_type,
                    'default': interfaces.IDefaultAction.providedBy(action.component)}

        return map(renderAction, self.actionWidgets)

    def updateForm(self):
        convert_request_form_to_unicode(self.request.form)
        self.update()
        form, action, status = self.updateActions()
        if status is FAILURE:
            # Render correctly the validation errors
            for error in form.formErrors:
                self.send_message(error.title, type="error")
        self.updateWidgets()
        info = {'ifaces': ['popup'],
                'success': status == SUCCESS}
        if interfaces.IRESTRefreshAction.providedBy(action):
            info['refresh'] = action.refresh
        success_only = interfaces.IRESTSuccessAction.providedBy(action)
        if not (success_only and status == SUCCESS):
            actions = self.renderActions()

            def findDefault(actions):
                candidates = filter(itemgetter('default'), actions)
                if not candidates:
                    candidates = actions
                return candidates[0]['name'] if candidates else None

            info.update(
                {'label': self.translate(self.label),
                 'widgets': self.render(),
                 'prefix': self.prefix,
                 'actions': actions,
                 'default_action': findDefault(actions)})
        result = {'content': info}
        notifications = self.get_notifications()
        if notifications is not None:
            result['notifications'] = notifications
        resources = get_resources(self.request)
        if resources is not None:
            result['resources'] = resources
        return result


class RESTPopupForm(UIREST, PopupCanvas):
    grok.baseclass()

    def __init__(self, context, request):
        UIREST.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def GET(self):
        return self.json_response(self.updateForm())

    def POST(self):
        return self.json_response(self.updateForm())


class PopupForm(PopupCanvas, Form):
    grok.baseclass()

    def __call__(self):
        """Popup form as a view.
        """
        self.response.setHeader('Content-Type', 'application/json')
        return json.dumps(self.updateForm())


class RESTFormTemplate(pt.PageTemplate):
    pt.view(PopupCanvas)
