# -*- coding: utf-8 -*-
# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from megrok import pagetemplate as pt
from infrae import rest
from zope.i18n import translate

from zeam.form.base.markers import SUCCESS
from zeam.form.base.form import FormCanvas
from zeam.form.silva.form import SilvaFormData
from zeam.form.silva import interfaces
from zeam.form.silva.utils import convert_request_form_to_unicode


REST_ACTIONS_TO_TOKEN = [
    (interfaces.IRESTCloseOnSuccessAction, 'close_on_success'),
    (interfaces.IRESTCloseAction, 'close'),
    (interfaces.IAction, 'send')]


class RESTForm(SilvaFormData, rest.REST, FormCanvas):
    grok.baseclass()

    def __init__(self, context, request):
        # XXX I loved super
        rest.REST.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def __translate(self, message):
        return translate(
            message, target_language=self.i18nLanguage, context=self.request)

    def renderActions(self):
        def renderAction(action):
            for rest_action, action_type in REST_ACTIONS_TO_TOKEN:
                if rest_action.providedBy(action.component):
                    break
            return {'label': self.__translate(action.title),
                    'name': action.identifier,
                    'action': action_type}
        return map(renderAction, self.actionWidgets)

    def processForm(self):
        action, status = self.updateActions()
        self.updateWidgets()
        info = {}
        info['success'] = status == SUCCESS
        success_only = interfaces.IRESTCloseOnSuccessAction.providedBy(action)
        if not (success_only and status == SUCCESS):
            info.update({
                    'label': self.__translate(self.label),
                    'widgets': self.render(),
                    'actions': self.renderActions()})
        return self.json_response(info)

    def GET(self):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm()

    def POST(self):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm()


class RESTFormTemplate(pt.PageTemplate):
    pt.view(RESTForm)
