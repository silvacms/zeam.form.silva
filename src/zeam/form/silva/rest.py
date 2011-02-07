# -*- coding: utf-8 -*-
# Copyright (c) 2010-2011 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from five import grok
from infrae import rest
from megrok import pagetemplate as pt
from silva.core.interfaces import IVersionedContent
from silva.core.smi.interfaces import ISMILayer
from zope.i18n import translate
from zope.interface import alsoProvides

from zeam.form.base.form import FormCanvas
from zeam.form.base.interfaces import IFormCanvas
from zeam.form.base.markers import SUCCESS
from zeam.form.base.widgets import getWidgetExtractor
from zeam.form.silva import interfaces
from zeam.form.silva.form import SilvaDataManager
from zeam.form.silva.form import SilvaFormData, SMIComposedForm
from zeam.form.silva.utils import convert_request_form_to_unicode
from zeam.form.ztk import validation


REST_ACTIONS_TO_TOKEN = [
    (interfaces.IRESTCloseOnSuccessAction, 'close_on_success'),
    (interfaces.IRESTCloseAction, 'close'),
    (interfaces.IAction, 'send')]


class RESTValidatorForm(SilvaFormData, rest.REST):
    grok.name('form-validate')
    grok.context(IFormCanvas)

    def __translate(self, message):
        return translate(
            message, target_language=self.i18nLanguage, context=self.request)

    def validateField(self, name, value):
        # Inject the value in form with the correct name and decode it.
        self.request.form[name] = value
        convert_request_form_to_unicode(self.request.form)

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
                        info['error'] = self.__translate(error)
                    break
        return self.json_response(info)

    def GET(self, name, value):
        return self.validateField(name, value)

    def POST(self, name, value):
        return self.validateField(name, value)


class RESTRefreshForm(rest.REST):
    grok.name('form-refresh')
    grok.context(SMIComposedForm)

    def processForm(self, identifier):
        form = self.context.getSubForm(identifier)
        if form is None:
            self.response.setStatus(404)
            return ''
        action, status = form.updateActions()
        form.updateWidgets()
        return self.json_response(
            {'form': form.render(),
             'success': status == SUCCESS})

    def GET(self, identifier):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm(identifier)

    def POST(self, identifier):
        convert_request_form_to_unicode(self.request.form)
        return self.processForm(identifier)


class RESTPopupForm(SilvaFormData, rest.REST, FormCanvas):
    grok.baseclass()

    def __init__(self, context, request):
        # Our custom widgets are registered on ISMILayer. Apply it as well
        alsoProvides(request, ISMILayer)
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
        if interfaces.IRESTRefreshAction.providedBy(action):
            info['refresh'] = action.refresh
        success_only = interfaces.IRESTSuccessAction.providedBy(action)
        if not (success_only and status == SUCCESS):
            actions = self.renderActions()
            info.update(
                {'label': self.__translate(self.label),
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


class RESTKupuEditProperties(RESTPopupForm):
    grok.baseclass()
    grok.name('kupu-properties')

    ignoreContent = False
    dataManager = SilvaDataManager
    dataValidators = [validation.InvariantsValidation]

    def setContentData(self, content):
        original_content = content
        if IVersionedContent.providedBy(original_content):
            content = original_content.get_editable()
            if content is None:
                content = original_content.get_previewable()
        super(RESTKupuEditProperties, self).setContentData(content)


class RESTKupuTemplate(pt.PageTemplate):
    pt.view(RESTKupuEditProperties)
