from Acquisition import aq_base

from five import grok
from megrok import pagetemplate as pt
from zeam.form import base, composed, layout
from zeam.form.base import FAILURE
from zeam.form.base.actions import Action
from zeam.form.base.datamanager import BaseDataManager
from zeam.form.base.fields import Field, Fields
from zeam.form.base.interfaces import IWidget, IForm, IField
from zeam.form.base.widgets import FieldWidget
from zeam.form.ztk.actions import EditAction, CancelAction
from zeam.form.ztk.fields import InterfaceSchemaFieldFactory
from zeam.form.silva.interfaces import IDefaultAddFields

from zope.configuration.name import resolve
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.i18n.locales import locales, LoadLocaleError
from zope.i18nmessageid import MessageFactory

from silva.core.conf.utils import getFactoryName
from silva.core.interfaces.content import IVersionedContent
from silva.core.smi.interfaces import ISMILayer
from Products.Silva.ExtensionRegistry import extensionRegistry


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


class AddAction(Action):

    def add(self, parent, data, form):
        """Purely create the object. This method can be overriden to
        support custom creation needs.
        """
        addable = filter(lambda a: a['name'] == form.__name__,
                         extensionRegistry.get_addables())
        if len(addable) != 1:
            raise ValueError, "Content cannot be found. " \
               "Check that the name of add is the meta type of your content."
        addable = addable[0]
        factory = getattr(resolve(addable['instance'].__module__),
                          getFactoryName(addable['instance']))
        # Build the content
        obj_id = str(data['id'])
        factory(parent, obj_id, data['title'])
        obj = getattr(parent, obj_id)
        #now move to position, if 'add_object_position' is in the request
        position = form.request.get('add_object_position', None)
        if position:
            try:
                position = int(position)
                if position >= 0:
                    parent.move_to([obj_id], position)
            except ValueError:
                pass
        return obj

    def __call__(self, form):
        data, errors = form.extractData()
        if form.errors:
            return FAILURE
        parent = form.context.aq_inner
        obj = self.add(parent, data, form)
        form.setContentData(obj)
        editable_obj = obj.get_editable()
        for key, value in data.iteritems():
            if key not in IDefaultAddFields:
                setattr(editable_obj, key, value)
        form.redirect(self.nextURL(form, obj))

    def nextURL(self, form, content):
        return '%s/edit' % content.aq_parent.absolute_url()


class AddAndEditAction(AddAction):

    def nextURL(self, form, content):
        return '%s/edit' % content.absolute_url()


class MetaTypeField(Field):
    mode = 'hidden'
    ignoreContent = True

    def __init__(self, name, value, identifier=None):
        super(MetaTypeField, self).__init__(name, identifier=identifier)
        self.defaultValue = value


class HiddenWidget(FieldWidget):
    grok.implements(IWidget)
    grok.adapts(IField, IForm, None)
    grok.name('hidden')


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
        CancelAction(_(u'cancel')),)


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
        CancelAction(_(u"cancel")))

    def setContentData(self, content):
        if IVersionedContent.providedBy(content):
            content = content.get_editable()
        super(SMIEditForm, self).setContentData(content)
