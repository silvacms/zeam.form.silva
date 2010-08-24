# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Acquisition import aq_base
from zExceptions import Redirect

from five import grok
from megrok import pagetemplate as pt

from zeam.form import base, composed, table, viewlet
from zeam.form.base.datamanager import BaseDataManager
from zeam.form.base.fields import Fields
from zeam.form.base.markers import DISPLAY, SUCCESS, NO_VALUE

from zeam.form.silva.interfaces import ISilvaFormData
from zeam.form.silva.utils import find_locale, convert_request_form_to_unicode
from zeam.form.silva.actions import CancelAddAction, CancelEditAction
from zeam.form.silva.actions import EditAction, ExtractedDecoratedAction


from infrae.layout.interfaces import IPage, ILayoutFactory
from grokcore.view.meta.views import default_view_name

from Products.Silva.ExtensionRegistry import extensionRegistry

from zope import component
from zope.configuration.name import resolve
from zope.publisher.publish import mapply
from zope.i18n.interfaces import IUserPreferredLanguages


from silva.core.conf.utils import getFactoryName
from silva.core.conf.interfaces import ITitledContent
from silva.core.interfaces.content import IVersionedContent
from silva.core.messages.interfaces import IMessageService
from silva.core.smi.interfaces import IEditTab, ISMITabIndex
from silva.core.smi.interfaces import ISMILayer, ISMINavigationOff
from silva.translations import translate as _


class SilvaFormData(object):
    grok.implements(ISilvaFormData)

    @property
    def i18nLanguage(self):
        adapter = IUserPreferredLanguages(self.request)
        languages = adapter.getPreferredLanguages()
        if languages:
            return languages[0]
        return 'en'

    def send_message(self, message, type=u""):
        service = component.getUtility(IMessageService)
        service.send(message, self.request, namespace=type)

    @apply
    def status():
        def get(self):
            try:
                return self.__status
            except AttributeError:
                return u''
        def set(self, value):
            self.send_message(value, type=u"feedback")
            self.__status = value
        return property(get, set)


class ZopeForm(object):
    """Simple Zope Form.
    """
    grok.baseclass()

    @property
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


class SilvaForm(SilvaFormData):
    """Form in Silva.
    """
    grok.baseclass()
    grok.implements(IPage)

    def __init__(self, context, request):
        super(SilvaForm, self).__init__(context, request)
        self.__name__ = self.__view_name__
        self.layout = None

    @property
    def tab_name(self):
        return grok.name.bind().get(self, default=default_view_name)

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


class ZMISubForm(composed.SubForm):
    """ZMI Composed forms.
    """
    grok.baseclass()


class ZMISubFormTemplate(pt.PageTemplate):
    pt.view(ZMISubForm)


class SMIForm(SilvaForm, base.Form):
    """Regular SMI form.
    """
    grok.baseclass()
    grok.layer(ISMILayer)
    grok.require('silva.ChangeSilvaContent')


class SMIFormTemplate(pt.PageTemplate):
    pt.view(SMIForm)


class SMIComposedForm(SilvaForm, composed.ComposedForm):
    """SMI Composed forms.
    """
    grok.baseclass()
    grok.layer(ISMILayer)
    grok.require('silva.ChangeSilvaContent')


class SMIComposedFormTemplate(pt.PageTemplate):
    pt.view(SMIComposedForm)


class SMISubForm(SilvaFormData, composed.SubForm):
    """SMI Sub forms.
    """
    grok.baseclass()


class SMISubFormTemplate(pt.PageTemplate):
    pt.view(SMISubForm)


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
    grok.implements(IEditTab, ISMINavigationOff)
    grok.require('silva.ChangeSilvaContent')

    tab = 'edit'
    tab_name = 'tab_edit'

    fields = Fields(ITitledContent)
    dataManager = SilvaDataManager
    ignoreContent = True
    actions = base.Actions(CancelAddAction(_(u'cancel')))

    def _add(self, parent, data):
        """Purely create the object. This method can be overriden to
        support custom creation needs.
        """
        # Search for an addable and a factory
        addable = filter(lambda a: a['name'] == self.__name__,
                         extensionRegistry.get_addables())
        if len(addable) != 1:
            raise ValueError(
                u"Content cannot be found. "
                u"Check that the name of add is the meta type of your content.")
        addable = addable[0]
        factory = getattr(resolve(addable['instance'].__module__),
                          getFactoryName(addable['instance']))

        # Build the content
        identifier = str(data['id'])
        factory(parent, identifier, data['title'])
        content = getattr(parent, identifier)

        # Now move to position, if 'add_object_position' is in the request
        position = self.request.form.get('add_object_position', None)
        if position:
            try:
                position = int(position)
                if position >= 0:
                    parent.move_to([identifier], position)
            except ValueError:
                pass

        # Set from value
        editable_content = self.dataManager(content.get_editable())
        for key, value in data.iteritems():
            if key not in ITitledContent and value is not NO_VALUE:
                editable_content.set(key, value)
        return content

    @base.action(
        _(u'save + edit'),
        identifier='save_edit',
        description=_(u"create the content and go on its edit view"),
        factory=ExtractedDecoratedAction)
    def save_edit(self, data):
        content = self._add(self.context, data)
        self.status = _(u'Added ${meta_type}',
                        mapping={'meta_type': self.__name__})
        self.redirect(self.url(content, name="edit"))
        return SUCCESS

    @base.action(
        _(u'save'),
        description=_(u"create the content and go back to the folder view"),
        factory=ExtractedDecoratedAction)
    def save(self, data):
        self._add(self.context, data)
        self.status = _(u'Added ${meta_type}',
                        mapping={'meta_type': self.__name__})
        self.redirect(self.url(name="edit"))
        return SUCCESS


class SMIAddFormTemplate(pt.PageTemplate):
    pt.view(SMIAddForm)


class SMIEditForm(SMIForm):
    """SMI Edit form.
    """
    grok.baseclass()
    grok.name('tab_edit')
    grok.require('silva.ChangeSilvaContent')
    grok.implements(IEditTab, ISMITabIndex)

    tab = 'edit'

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


class SMIViewletForm(SilvaFormData, viewlet.ViewletForm):
    """ Base form in viewlet
    """
    grok.baseclass()

    def available(self):
        for action in self.actions:
            if action.available(self):
                return True
        return False

    def redirect(self, url):
        # Raise redirect exception to be not to render the current
        # page anymore.
        raise Redirect(url)
