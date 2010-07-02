from Acquisition import aq_base

from five import grok
from megrok import pagetemplate as pt
from zope.component import getUtility
from zeam.form import base, composed
from zeam.form.base.datamanager import BaseDataManager
from zeam.form.base.fields import Fields
from zeam.form.base.markers import DISPLAY

from zeam.form.ztk.actions import EditAction
from zeam.form.ztk.fields import InterfaceSchemaFieldFactory
from zeam.form.silva.actions import *
from zeam.form.viewlet import form as viewletform

from infrae.layout.interfaces import IPage, ILayoutFactory

from zope import component
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import locales, LoadLocaleError
from zope.i18nmessageid import MessageFactory
from zope.publisher.publish import mapply

from silva.core.interfaces.content import IVersionedContent
from silva.core.smi.interfaces import ISMILayer, ISMINavigationOff
from silva.core.messages.interfaces import IMessageService


_ = MessageFactory("silva")


def find_locale(request):
    envadapter = IUserPreferredLanguages(request, None)
    if envadapter is None:
        return None

    langs = envadapter.getPreferredLanguages()
    for httplang in langs:
        parts = (httplang.split('-') + [None, None])[:3]
        try:
            return locales.getLocale(*parts)
        except LoadLocaleError:
            # Just try the next combination
            pass
    else:
        # No combination gave us an existing locale, so use the default,
        # which is guaranteed to exist
        return locales.getLocale(None, None, None)


def decode_to_unicode(string):
    if not isinstance(string, str):
        return string
    try:
        return string.decode('utf-8')
    except UnicodeDecodeError:
        # Log
        return string


def convert_request_form_to_unicode(form):
    for key, value in form.iteritems():
        if isinstance(value, list):
            form[key] = [decode_to_unicode(i) for i in value]
        else:
            form[key] = decode_to_unicode(value)



class SilvaFormData(object):

    @property
    def i18nLanguage(self):
        return self.request.get('LANGUAGE', 'en')

    def send_message(self, message, type=u""):
        service = getUtility(IMessageService)
        service.send(message, self.request, namespace=type)


class ZopeForm(object):
    """Simple Zope Form.
    """
    grok.baseclass()

    @property
    def i18nLanguage(self):
        return self.request.get('LANGUAGE', 'en')

    def __init__(self, context, request):
        super(ZopeForm, self).__init__(context, request)
        self.__name__ = self.__view_name__

    def __call__(self):
        if not hasattr(self.request, 'locale'):
            # This is not pretty, but no choice.
            self.request.locale = find_locale(self.request)
        convert_request_form_to_unicode(self.request.form)

        return super(ZopeForm, self).__call__()


class SilvaForm(SilvaFormData):
    """Form in Silva.
    """
    grok.baseclass()
    grok.implements(IPage)

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


class ZMIFormTemplate(pt.PageTemplate):
    pt.view(ZMIForm)


class ZMIComposedForm(ZopeForm, composed.ComposedForm):
    """ZMI Composed forms.
    """
    grok.baseclass()


class ZMIComposedFormTemplate(pt.PageTemplate):
    pt.view(ZMIComposedForm)


class SMIForm(SilvaForm, base.Form):
    """Regular SMI form.
    """
    grok.baseclass()
    grok.layer(ISMILayer)


class SMIFormTemplate(pt.PageTemplate):
    pt.view(SMIForm)


class SMIAddForm(SMIForm):
    """ SMI add form
    """
    grok.baseclass()
    grok.implements(ISMINavigationOff)
    grok.require('silva.ChangeSilvaContent')

    template = grok.PageTemplate(filename="form_templates/smiaddform.cpt")

    tab = 'edit'
    tab_name = 'tab_edit'

    fields = Fields(IDefaultAddFields, factory=InterfaceSchemaFieldFactory)
    dataManager = SilvaDataManager
    ignoreContent = True
    actions = base.Actions(
        AddAction(_(u'save')),
        AddAndEditAction(_(u'save + edit')),
        CancelAddAction(_(u'cancel')),)


class SMIEditForm(SMIForm):
    """SMI Edit form.
    """
    grok.baseclass()
    grok.name('tab_edit')
    grok.require('silva.ChangeSilvaContent')

    tab = 'edit'
    tab_name = 'tab_edit'

    dataManager = SilvaDataManager
    ignoreContent = False
    actions = base.Actions(
        EditAction(_(u"save")),
        CancelEditAction(_(u"cancel")))

    def update(self):
        """ If we have a versioned content and it has a published/approved
        version, the we set the form in display mode.
        """
        super(SMIEditForm, self).update()
        if IVersionedContent.providedBy(self.context):
            if not self.context.get_editable():
                self.mode = DISPLAY
                self.actions = base.Actions()

    def setContentData(self, content):
        original_content = content
        if IVersionedContent.providedBy(original_content):
            content = original_content.get_editable()
            if content is None:
                content = original_content.get_previewable()
        super(SMIEditForm, self).setContentData(content)


class SMIViewletForm(viewletform.ViewletForm, SilvaFormData):
    """ Base form in viewlet
    """
    grok.baseclass()

    def available(self):
        for action in self.actions:
            if action.available(self):
                return True
        return False

