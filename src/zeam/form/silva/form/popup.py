# -*- coding: utf-8 -*-
# Copyright (c) 2011-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import json
from operator import itemgetter

from five import grok
from megrok import pagetemplate as pt
from zope.traversing.browser import absoluteURL

from silva.ui.rest.base import UIREST, SMITransaction
from silva.ui.rest import helper
from silva.ui.rest.exceptions import RESTRedirectHandler
from zeam.form.base.form import FormCanvas, Form
from zeam.form.base.markers import SUCCESS, FAILURE
from zeam.form.silva import interfaces
from zeam.form.silva.utils import SilvaFormData
from zeam.form.silva.utils import convert_request_form_to_unicode


REST_ACTIONS_TO_TOKEN = [
    (interfaces.IRESTCloseOnSuccessAction, 'close_on_success'),
    (interfaces.IRESTCloseAction, 'close'),
    (interfaces.IAction, 'send')]


class RefreshExtraPayload(grok.Adapter):
    grok.context(interfaces.IRESTRefreshAction)
    grok.provides(interfaces.IRESTExtraPayloadProvider)

    def get_extra_payload(self, form):
        return {'refresh': self.context.refresh}


class PopupCanvas(helper.UIHelper, SilvaFormData, FormCanvas):
    grok.baseclass()
    novalidation = False

    def update(self):
        pass

    def renderActions(self):

        def renderAction(action):
            for rest_action, action_type in REST_ACTIONS_TO_TOKEN:
                if rest_action.providedBy(action.component):
                    break
            return {
                'label': self.translate(action.title),
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
                'success': status is SUCCESS}
        if status is SUCCESS:
            extra = interfaces.IRESTExtraPayloadProvider(action, None)
            if extra is not None:
                info['extra'] = extra.get_extra_payload(self)
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
                 'url': absoluteURL(self, self.request),
                 'default': findDefault(actions),
                 'validation': not self.novalidation})
        return {'content': info}

    def renderForm(self):
        with SMITransaction(self):
            data = self.updateForm()

        for provider in self.needed():
            provider(self, data)

        return data


class RESTPopupForm(PopupCanvas, UIREST):
    grok.baseclass()

    def __init__(self, context, request):
        UIREST.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def GET(self):
        try:
            return self.json_response(self.renderForm())
        except RESTRedirectHandler as handler:
            return handler.publish(self)

    def POST(self):
        try:
            return self.json_response(self.renderForm())
        except RESTRedirectHandler as handler:
            return handler.publish(self)


class PopupForm(PopupCanvas, Form):
    grok.baseclass()

    def __call__(self):
        """Popup form as a view.
        """
        self.response.setHeader('Content-Type', 'application/json')
        return json.dumps(self.renderForm())


class RESTFormTemplate(pt.PageTemplate):
    pt.view(PopupCanvas)
