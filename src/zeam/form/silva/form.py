# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Acquisition import aq_base
from zExceptions import Redirect

from five import grok
from megrok import pagetemplate as pt

from zeam.form.base.form import FormCanvas
from zeam.form.base.actions import Actions, action
from zeam.form import base, composed, table, viewlet
from zeam.form.base.datamanager import BaseDataManager
from zeam.form.base.fields import Fields
from zeam.form.base.markers import SUCCESS, FAILURE, NO_VALUE
from zeam.form.ztk import validation

from zeam.form.silva.interfaces import ISilvaFormData
from zeam.form.silva.utils import find_locale, convert_request_form_to_unicode
from zeam.form.silva.actions import CancelAddAction, CancelEditAction
from zeam.form.silva.actions import EditAction, ExtractedDecoratedAction

from infrae.layout.interfaces import IPage, ILayoutFactory

from Products.Silva.icon import get_icon_url
from Products.Silva.ExtensionRegistry import extensionRegistry

from zope import component
from zope.cachedescriptors.property import CachedProperty
from zope.configuration.name import resolve
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.publisher.publish import mapply

from silva.core.conf.interfaces import ITitledContent
from silva.core.conf.utils import getFactoryName
from silva.core.interfaces.content import IVersionedContent
from silva.core.layout.interfaces import ISilvaLayer
from silva.core.messages.interfaces import IMessageService
from silva.core.views.views import HTTPHeaderView
from silva.translations import translate as _
from silva.ui.rest.base import PageREST, RedirectToPage


REST_ACTIONS_TO_TOKEN = []

class SilvaFormData(object):
    grok.implements(ISilvaFormData)

    @CachedProperty
    def i18nLanguage(self):
        adapter = IUserPreferredLanguages(self.request)
        languages = adapter.getPreferredLanguages()
        if languages:
            return languages[0]
        return 'en'

    def send_message(self, message, type=u""):
        service = component.getUtility(IMessageService)
        service.send(message, self.request, namespace=type)


class ZopeForm(object):
    """Simple Zope Form.
    """
    grok.baseclass()
    dataValidators = [validation.InvariantsValidation]

    @CachedProperty
    def i18nLanguage(self):
        adapter = IUserPreferredLanguages(self.request)
        languages = adapter.getPreferredLanguages()
        if languages:
            return languages[0]
        return 'en'

    def __init__(self, context, request):
        super(ZopeForm, self).__init__(context, request)
        self.__name__ = self.__view_name__

    def __call__(self):
        if not hasattr(self.request, 'locale'):
            # This is not pretty, but no choice.
            self.request.locale = find_locale(self.request)
        convert_request_form_to_unicode(self.request.form)

        return super(ZopeForm, self).__call__()


class SilvaForm(HTTPHeaderView, SilvaFormData):
    """Form in Silva.
    """
    grok.baseclass()
    grok.implements(IPage)
    dataValidators = [validation.InvariantsValidation]

    def __init__(self, context, request):
        super(SilvaForm, self).__init__(context, request)
        self.__name__ = self.__view_name__
        self.layout = None

    def default_namespace(self):
        namespace = super(SilvaForm, self).default_namespace()
        namespace['layout'] = self.layout
        return namespace

    def content(self):
        return self.render()

    def __call__(self):
        self.setHTTPHeaders()
        if not hasattr(self.request, 'locale'):
            # This is not pretty, but no choice.
            self.request.locale = find_locale(self.request)
        convert_request_form_to_unicode(self.request.form)

        layout_factory = component.getMultiAdapter(
            (self.request, self.context,), ILayoutFactory)
        self.layout = layout_factory(self)

        mapply(self.update, (), self.request)
        if self.request.response.getStatus() in (302, 303):
            # A redirect was triggered somewhere in update(). Don't
            # continue processing the form
            return

        self.updateForm()
        if self.request.response.getStatus() in (302, 303):
            return

        return self.layout(self)


class SilvaDataManager(BaseDataManager):
    """Try to use in priority set_ and get_ methods when setting and
    getting values on an object, paying attention to the Acquisition.
    """

    def get(self, identifier):
        if hasattr(aq_base(self.content), 'get_%s' % identifier):
            getter = getattr(self.content, 'get_%s' % identifier)
            return getter()
        if not hasattr(aq_base(self.content), identifier):
            raise KeyError(identifier)
        return getattr(self.content, identifier)

    def set(self, identifier, value):
        if hasattr(aq_base(self.content), 'set_%s' % identifier):
            setter = getattr(self.content, 'set_%s' % identifier)
            return setter(value)
        return setattr(self.content, identifier, value)


class ZMIForm(ZopeForm, base.Form):
    """Regular ZMI forms.
    """
    grok.baseclass()
    grok.require('zope2.ViewManagementScreens')


class ZMIFormTemplate(pt.PageTemplate):
    pt.view(ZMIForm)


class ZMIComposedForm(ZopeForm, composed.ComposedForm):
    """ZMI Composed forms.
    """
    grok.baseclass()
    grok.require('zope2.ViewManagementScreens')


class ZMIComposedFormTemplate(pt.PageTemplate):
    pt.view(ZMIComposedForm)


class ZMISubForm(composed.SubForm):
    """ZMI Composed forms.
    """
    grok.baseclass()


class ZMISubFormTemplate(pt.PageTemplate):
    pt.view(ZMISubForm)


class SMIForm(SilvaFormData, PageREST, FormCanvas):
    """Regular SMI form.
    """
    grok.baseclass()
    grok.name('silva.ui.content')
    grok.require('silva.ChangeSilvaContent')

    dataValidators = [validation.InvariantsValidation]
    dataManager = SilvaDataManager

    def __init__(self, context, request):
        PageREST.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def renderActions(self):
        def renderAction(action):
            return {'label': action.title,
                    'name': action.identifier}
        return map(renderAction, self.actionWidgets)

    def payload(self):
        convert_request_form_to_unicode(self.request.form)
        action, status = self.updateActions()
        self.updateWidgets()
        actions = self.renderActions()
        return {'ifaces': ['form'],
                'success': status == SUCCESS,
                'html': self.render(),
                'actions': actions,
                'default': actions[0]['name'] if actions else None}


class SMIFormTemplate(pt.PageTemplate):
    pt.view(SMIForm)


class PublicForm(SilvaForm, base.Form):
    """Regular SMI form.
    """
    grok.baseclass()
    grok.layer(ISilvaLayer)
    grok.require('zope.Public')


class SMIComposedForm(SilvaForm, composed.ComposedForm):
    """SMI Composed forms.
    """
    grok.baseclass()
    grok.require('silva.ChangeSilvaContent')

    @property
    def icon_url(self):
        return get_icon_url(self.context, self.request)


class SMIComposedFormTemplate(pt.PageTemplate):
    pt.view(SMIComposedForm)


class SMISubForm(SilvaFormData, composed.SubForm):
    """SMI Sub forms.
    """
    grok.baseclass()


class SMISubFormTemplate(pt.PageTemplate):
    pt.view(SMISubForm)


class SMISubFormGroup(SilvaFormData, composed.SubFormGroup):
    """SMI sub form group.
    """
    grok.baseclass()


class SMISubFormGroupTemplate(pt.PageTemplate):
    pt.view(SMISubFormGroup)


class SMISubTableForm(SilvaFormData, table.SubTableForm):
    """SMI Sub table forms.
    """
    grok.baseclass()


class SMISubTableFormTemplate(pt.PageTemplate):
    pt.view(SMISubTableForm)


class SMIAddForm(SMIForm):
    """ SMI add form
    """
    grok.baseclass()

    prefix = 'addform'

    fields = Fields(ITitledContent)
    ignoreContent = True
    actions = Actions()

    def _add(self, parent, data):
        """Purely create the object. This method can be overriden to
        support custom creation needs.
        """
        # Search for an addable and a factory
        addable = extensionRegistry.get_addable(self.__name__)
        if not addable:
            raise ValueError(u"Content factory cannot be found. ")

        factory = getattr(
            resolve(addable['instance'].__module__),
            getFactoryName(addable['instance']))

        # Build the content
        identifier = str(data.getWithDefault('id'))
        factory(parent, identifier, data.getWithDefault('title'))
        content = getattr(parent, identifier)

        self._edit(parent, content, data)
        return content

    def _edit(self, parent, content, data):
        # Set from value
        editable_content = self.dataManager(content.get_editable())
        for key, value in data.iteritems():
            if key not in ITitledContent and value is not NO_VALUE:
                editable_content.set(key, value)

    @action(
        _(u'save'),
        description=_(u"create the content"),
        factory=ExtractedDecoratedAction)
    def save(self, data):
        try:
            content = self._add(self.context, data)
        except ValueError, error:
            self.send_message(error.args[0], type=u"error")
            return FAILURE
        self.send_message(
            _(u'Added ${meta_type}.', mapping={'meta_type': self.__name__}),
            type="feedback")
        raise RedirectToPage(content)

    actions.append(CancelAddAction())


class SMIEditForm(SMIForm):
    """SMI Edit form.
    """
    grok.baseclass()

    prefix = 'editform'

    dataManager = SilvaDataManager
    ignoreContent = False
    actions = Actions(
        EditAction(),
        CancelEditAction())

    def setContentData(self, content):
        original_content = content
        if IVersionedContent.providedBy(original_content):
            content = original_content.get_editable()
            if content is None:
                content = original_content.get_previewable()
        super(SMIEditForm, self).setContentData(content)


class SMIViewletForm(SilvaFormData, viewlet.ViewletForm):
    """ Base form in viewlet
    """
    grok.baseclass()

    def available(self):
        for action in self.actions:
            if action.available(self):
                return True
        return False

    def update(self):
        if not hasattr(self.request, 'locale'):
            self.request.locale = find_locale(self.request)
        convert_request_form_to_unicode(self.request.form)
        return super(SMIViewletForm, self).update()

    def redirect(self, url):
        # Raise redirect exception to be not to render the current
        # page anymore.
        raise Redirect(url)

PublicViewletForm = SMIViewletForm


class SMIContentProviderForm(SilvaFormData, viewlet.ViewletManagerForm):
    grok.baseclass()

    def update(self):
        if not hasattr(self.request, 'locale'):
            self.request.locale = find_locale(self.request)
        convert_request_form_to_unicode(self.request.form)
        return super(SMIContentProviderForm, self).update()

    def redirect(self, url):
        # Raise redirect exception to be not to render the current
        # page anymore.
        raise Redirect(url)

PublicContentProviderForm = SMIContentProviderForm
