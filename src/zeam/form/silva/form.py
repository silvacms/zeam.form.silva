from Acquisition import aq_base

from five import grok
from megrok import pagetemplate as pt
from zeam.form import base, composed, layout
from zeam.form.base.datamanager import BaseDataManager
from zeam.form.base.fields import Fields

from zeam.form.ztk.actions import EditAction
from zeam.form.ztk.fields import InterfaceSchemaFieldFactory
from zeam.form.silva.actions import *

from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import locales, LoadLocaleError
from zope.i18nmessageid import MessageFactory

from silva.core.interfaces.content import IVersionedContent
from silva.core.smi.interfaces import ISMILayer


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


class SilvaForm(SilvaFormData):
    """Form in Silva.
    """
    grok.baseclass()
    # Inherit from Acquisition for Zope 2.

    def __init__(self, context, request):
        super(SilvaForm, self).__init__(context, request)
        self.__name__ = self.__view_name__

    def __call__(self):
        if not hasattr(self.request, 'locale'):
            # This is not pretty, but no choice.
            self.request.locale = find_locale(self.request)
        convert_request_form_to_unicode(self.request.form)
        return super(SilvaForm, self).__call__()


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


class ZMIForm(SilvaForm, base.Form):
    """Regular ZMI forms.
    """
    grok.baseclass()


class ZMIFormTemplate(pt.PageTemplate):
    pt.view(ZMIForm)


class ZMIComposedForm(SilvaForm, composed.ComposedForm):
    """ZMI Composed forms.
    """
    grok.baseclass()


class ZMIComposedFormTemplate(pt.PageTemplate):
    pt.view(ZMIComposedForm)


class SMIForm(SilvaForm, layout.Form):
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

    def setContentData(self, content):
        if IVersionedContent.providedBy(content):
            content = content.get_editable()
        super(SMIEditForm, self).setContentData(content)
