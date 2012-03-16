# Copyright (c) 2010 Infrae. All rights reserved.
# See also LICENSE.txt
# $Id$

from Acquisition import aq_base
from zExceptions import Redirect

from five import grok
from zope import interface, schema
from megrok import pagetemplate as pt
from zope.component.interfaces import ComponentLookupError

from zeam.form import base, composed, table, viewlet
from zeam.form.base.datamanager import BaseDataManager
from zeam.form.base.fields import Fields
from zeam.form.base.widgets import Widgets
from zeam.form.base.markers import DISPLAY, SUCCESS, FAILURE, NO_VALUE, HIDDEN
from zeam.form.ztk import validation

from zeam.form.silva.interfaces import ISilvaFormData
from zeam.form.silva.utils import find_locale, convert_request_form_to_unicode
from zeam.form.silva.actions import CancelAddAction, CancelEditAction
from zeam.form.silva.actions import EditAction, ExtractedDecoratedAction


from infrae.layout.interfaces import IPage, ILayoutFactory
from grokcore.view.meta.views import default_view_name

from Products.Silva.icon import get_icon_url, get_meta_type_icon_url
from Products.Silva.ExtensionRegistry import extensionRegistry

from zope import component
from zope.cachedescriptors.property import CachedProperty
from zope.configuration.name import resolve
from zope.i18n.interfaces import IUserPreferredLanguages
from zope.publisher.publish import mapply

from silva.core.interfaces import (IContentLayout, IVersionedContentLayout, 
                                   IDefaultContentTemplate)
from silva.core.conf.interfaces import ITitledContent
from silva.core.conf.utils import getFactoryName
from silva.core.interfaces.content import (IPublishable, IContainer,
                                           IVersionable)
from silva.core.layout.interfaces import ISilvaLayer
from silva.core.messages.interfaces import IMessageService
from silva.core.smi.interfaces import IAddingTab, IEditTabIndex
from silva.core.smi.interfaces import ISMILayer
from silva.core.views.views import HTTPHeaderView, ContentTemplateMixin
from silva.translations import translate as _


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


class SilvaForm(HTTPHeaderView, SilvaFormData, ContentTemplateMixin):
    """Form in Silva.
    """
    grok.baseclass()
    grok.implements(IPage)
    dataValidators = [validation.InvariantsValidation]

    def __init__(self, context, request):
        super(SilvaForm, self).__init__(context, request)
        self.__name__ = self.__view_name__
        self.layout = None

    @property
    def tab_name(self):
        # XXX should only be available for SMI
        return grok.name.bind().get(self, default=default_view_name)

    def default_namespace(self):
        namespace = super(SilvaForm, self).default_namespace()
        namespace['layout'] = self.layout
        return namespace

    def content(self):
        #wrap content around content layout template
        content = self.render()
        return self.wrap_if_necessary(content)

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
    
    def __init__(self, content):
        #if it's versionedcontent(or asset), the data
        # should be stored on the editable version NOT the content
        if IVersionable.providedBy(content):
            self.content = content.get_editable()
        else:
            self.content = content

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
    dataValidators = [validation.InvariantsValidation]


class ZMISubFormTemplate(pt.PageTemplate):
    pt.view(ZMISubForm)


class SMIForm(SilvaForm, base.Form):
    """Regular SMI form.
    """
    grok.baseclass()
    grok.layer(ISMILayer)
    grok.require('silva.ChangeSilvaContent')

    @property
    def icon_url(self):
        return get_icon_url(self.context, self.request)


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
    grok.layer(ISMILayer)
    grok.require('silva.ChangeSilvaContent')
    
    #whether to display a form tag around all subforms or not.  (default No)
    #  set to True to have a single set of actions for the composed form,
    #  using the subforms for grouping only.  (subforms should have
    #  suppress_form_tag=True and an empty actions list)
    suppress_form_tag = True
    
    @property
    def icon_url(self):
        return get_icon_url(self.context, self.request)


class SMIComposedFormTemplate(pt.PageTemplate):
    pt.view(SMIComposedForm)


class SMISubForm(SilvaFormData, composed.SubForm):
    """SMI Sub forms.
    """
    grok.baseclass()
    dataValidators = [validation.InvariantsValidation]
    
    #set this to True to suppress the rendering of the form tag.  Useful
    # if the subform is being used to group data, but the ComposedForm
    # has the actions.
    suppress_form_tag = False
    
    #it is more or less obvious which fields are required -- they have a '*'
    # next to them.  when there are many subforms on the page, seeing the
    # exact same notice below each isn't necessary.  Set to true to
    # disable the notice.
    suppress_required_notice = False


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


class IAddOptions(interface.Interface):
    position = schema.Int(
        title=_(u"add position"),
        description=_(
            u"Position in the container to which the content will be added."),
        default=0,
        min=0)
    return_url = schema.TextLine(
        title=_(u"URL to return to after adding"))


def add_position_available(form):
    if  'addform.options.position' not in form.request.form:
        return False
    addable = extensionRegistry.get_addable(form.__name__)
    return IPublishable.implementedBy(addable['instance'])


class SMIAddForm(SMIForm):
    """ SMI add form
    """
    grok.baseclass()
    grok.implements(IAddingTab)

    prefix = 'addform'
    tab = 'edit'

    fields = Fields(ITitledContent)
    dataManager = SilvaDataManager
    ignoreContent = True
    actions = base.Actions()
    optionFields = Fields(IAddOptions)
    optionFields['position'].prefix = 'options'
    optionFields['position'].mode = 'readonly'
    optionFields['position'].available = add_position_available
    optionFields['return_url'].mode = HIDDEN

    def updateWidgets(self):
        super(SMIAddForm, self).updateWidgets()
        optionWidgets = Widgets(form=self, request=self.request)
        optionWidgets.extend(self.optionFields)
        optionWidgets.update()
        self.fieldWidgets.extend(optionWidgets)

    @property
    def tab_name(self):
        return '+/' + self.__name__

    @property
    def icon_url(self):
        return get_meta_type_icon_url(self.__name__, self.request)

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
        #set these after, as they involve setting in the metdata,
        # and specifically the description is set on the default document
        # of containers (if present), so _edit (in FolderAddForm) needs
        # to run first
        st = data.getWithDefault('shorttitle')
        if st is not None:
            self.set_short_title(parent, content, st)
        desc = data.getWithDefault('description')
        if desc is not None:
            self.set_description(parent, content, desc)
        return content

    def _edit(self, parent, content, data):
        # Set from value
        editable_content = self.dataManager(content.get_editable())
        for key, value in data.iteritems():
            if key not in ITitledContent and value is not NO_VALUE:
                editable_content.set(key, value)
                
    def set_short_title(self, parent, content, shorttitle):
        #save shorttitle in metadata from form data
        editable_content = content.get_editable()
        sm = content.get_root().service_metadata
        sm_binding = sm.getMetadata(editable_content)
        sm_binding.setValues('silva-content', {'shorttitle': shorttitle})

    def set_description(self, parent, content, desc):
        #set description in metadata from form data
        editable_content = content.get_editable()
        # if this is a container add to default silva content (i.e. index, autoTOC)
        if IContainer.providedBy(editable_content):
            default = editable_content.get_default()
            if default:
                editable_content = default.get_editable()
        sm = content.get_root().service_metadata
        sm_binding = sm.getMetadata(editable_content)
        sm_binding.setValues('silva-extra', {'content_description': desc})

    def _move(self, parent, content):
        data, errors = self.extractData(self.optionFields)
        position = data.getWithDefault('position')
        if position > 0:
            # XXX bug in Folder to have move_to(2) you actually need 1.
            parent.move_to([content.getId()], position - 1)

    @base.action(
        _(u'save + edit'),
        identifier='save_edit',
        description=_(
            u"create the content and go on its edit view: alt-e"),
        accesskey=u'e',
        factory=ExtractedDecoratedAction)
    def save_edit(self, data):
        try:
            content = self._add(self.context, data)
            self._move(self.context, content)
        except ValueError, error:
            self.send_message(error, type="error")
            return FAILURE
        self.send_message(
            _(u'Added ${meta_type}.', mapping={'meta_type': self.__name__}),
            type="feedback")
        self.redirect(self.url(content, name="edit"))
        return SUCCESS

    @base.action(
        _(u'save'),
        description=_(
            u"create the content and go back to the folder view: alt-s"),
        accesskey=u's',
        factory=ExtractedDecoratedAction)
    def save(self, data):
        try:
            content = self._add(self.context, data)
            self._move(self.context, content)
        except ValueError, error:
            self.send_message(error.args[0], type=u"error")
            return FAILURE
        self.send_message(
            _(u'Added ${meta_type}.', mapping={'meta_type': self.__name__}),
            type="feedback")
        data, errors = self.extractData(self.optionFields)
        if data['return_url'] and data['return_url'] is not NO_VALUE:
            self.redirect(data['return_url'])
        else:
            self.redirect(self.url(name="edit"))
        return SUCCESS

    actions.append(CancelAddAction())


class SMIAddFormTemplate(pt.PageTemplate):
    pt.view(SMIAddForm)

class SMIEditFormBase(object):
    """Base class for any sort of SMI edit form.
    
    This base class takes care to use the correct version of the context object
    when updating the form or setting the content data.
    
    If the content is versioned and it is published/approved, the form is set
    to DISPLAY mode, and the previewable version is used.
    """
    grok.baseclass()
    
    dataManager = SilvaDataManager
    ignoreContent = False
    actions = base.Actions(
        EditAction(),
        CancelEditAction())

    def update(self):
        """ If we have a versioned content and it has a published/approved
        version, the we set the form in display mode.
        """
        super(SMIEditFormBase, self).update()
        if IVersionable.providedBy(self.context):
            if ((not self.context.get_editable()) or
                self.context.is_version_approval_requested()):
                self.mode = DISPLAY
                self.actions = base.Actions()

    def setContentData(self, content):
        original_content = content
        if IVersionable.providedBy(original_content):
            content = original_content.get_editable()
            if content is None:
                content = original_content.get_previewable()
        super(SMIEditFormBase, self).setContentData(content)


class SMIEditForm(SMIEditFormBase, SMIForm):
    """SMI Edit form.
    """
    grok.baseclass()
    grok.name('tab_edit')
    grok.implements(IEditTabIndex)

    prefix = 'editform'
    tab = 'edit'


class SMIComposedEditForm(SMIEditFormBase, SMIComposedForm):
    """
    A Silva Edit Form which contains other forms.
    
    This is useful if, on the SMI Edit screen, you want to have separate edit
    forms with separate actions, or want to use subforms to separate out
    related sets of configuration properties. In the latter case, you can use
    a ComposedEditAction on the ComposedForm, with no actions in the subforms,
    so there is a single "save" button.
    
    """
    grok.baseclass()
    grok.name('tab_edit')
    grok.implements(IEditTabIndex)

    prefix = 'editform'
    tab = 'edit'


class SMISubEditForm(SMIEditFormBase, SMISubForm):
    """
    An SMISubForm which is used on the edit screen, to edit a subset of
    a Silva object's data.
    
    This subclass is specific to editing Silva content.  Like SMIEditForm,
    it switches to the editable or previewable version of content as
    appropriate.
    
    """
    grok.baseclass()
    suppress_form_tag = False


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
