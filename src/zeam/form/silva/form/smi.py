# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from AccessControl.security import checkPermission

from five import grok
from megrok import pagetemplate as pt
from zope.interface import Interface
from zope.component import queryMultiAdapter
from zope.component import getMultiAdapter
from zope.configuration.name import resolve

from zeam.form import composed, table
from zeam.form.base.actions import Actions, action
from zeam.form.base.fields import Fields
from zeam.form.base.form import FormCanvas
from zeam.form.base.interfaces import IWidget, IAction
from zeam.form.base.markers import DISPLAY, SUCCESS, FAILURE, NO_VALUE
from zeam.form.composed.form import SubFormGroupBase
from zeam.form.ztk import validation

from Products.Silva.ExtensionRegistry import extensionRegistry

from silva.core import conf as silvaconf
from silva.core.conf.interfaces import ITitledContent
from silva.core.conf.utils import getFactoryName
from silva.core.views import views as silvaviews
from silva.core.interfaces.content import IVersionedObject
from silva.ui.interfaces import ISilvaUIDependencies
from silva.translations import translate as _
from silva.ui.rest import PageREST, RedirectToPage

from ..actions import CancelAddAction, CancelEditAction, CancelAction
from ..actions import EditAction, ExtractedDecoratedAction
from ..datamanager import SilvaDataManager
from ..interfaces import ISMIForm, IDefaultAction, IDisplayWidgetFactory
from ..utils import SilvaFormData
from ..utils import convert_request_form_to_unicode


class IFormSilvaUIResources(ISilvaUIDependencies):
    silvaconf.resource('smi.js')


class SMIFormPortlets(silvaviews.ViewletManager):
    """Report information on assets.
    """
    grok.context(Interface)
    grok.view(ISMIForm)
    grok.name('portlets')


class SMIDisplayWidgetFactory(object):
    grok.implements(IDisplayWidgetFactory)

    def __init__(self, form, request):
        self.form = form
        self.request = request

    def widget(self, field):
        if not field.available(self.form):
            return None
        mode = 'input' if IAction.providedBy(field) else 'display'
        return getMultiAdapter(
            (field, self.form, self.request),
            IWidget, name=mode)

    def extractor(self, field):
        # Read-only fields can not be extracted.
        return None


class SMIForm(SilvaFormData, PageREST, FormCanvas):
    """Regular SMI form.
    """
    grok.baseclass()
    grok.name('content')
    grok.require('silva.ChangeSilvaContent')
    grok.implements(ISMIForm)

    dataValidators = [validation.InvariantsValidation]
    dataManager = SilvaDataManager

    def __init__(self, context, request):
        PageREST.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def update(self):
        pass

    def redirect(self, url):
        raise RedirectToPage(url)

    def payload(self):
        convert_request_form_to_unicode(self.request.form)
        self.update()
        form, action, status = self.updateActions()
        if status is FAILURE:
            # Render correctly the validation errors
            for error in form.formErrors:
                self.send_message(error.title, type="error")
        self.updateWidgets()
        result = {'ifaces': ['form'],
                  'success': status == SUCCESS,
                  'forms': self.render()}
        portlets = queryMultiAdapter(
            (self.context, self.request, self), name='portlets')
        if portlets is not None:
            portlets.update()
            rendered_portlets = portlets.render().strip()
            if rendered_portlets:
                result['portlets'] = rendered_portlets
        return result


class SMIFormTemplate(pt.PageTemplate):
    pt.view(SMIForm)


class ConfigurationForm(SMIForm):
    grok.baseclass()
    grok.name('admin')
    grok.require('zope2.ViewManagementScreens')
    ignoreContent = False

    def get_menu_title(self):
        return self.label

    def get_menu_parent(self):
        parent = super(ConfigurationForm, self).get_menu_parent()
        parent['screen'] = 'admin'
        return parent


class SMITableForm(SMIForm, table.TableForm):
    """SMI table forms.
    """
    grok.baseclass()


class SMITableFormTemplate(pt.PageTemplate):
    pt.view(SMITableForm)


class SMIComposedForm(SilvaFormData, PageREST, SubFormGroupBase, FormCanvas):
    """SMI Composed forms.
    """
    grok.baseclass()
    grok.implements(ISMIForm)
    grok.require('silva.ChangeSilvaContent')

    def __init__(self, context, request):
        PageREST.__init__(self, context, request)
        SubFormGroupBase.__init__(self, context, request)
        FormCanvas.__init__(self, context, request)

    def payload(self):
        convert_request_form_to_unicode(self.request.form)
        self.update()
        form, action, status = SubFormGroupBase.updateActions(self)
        if action is None:
            form, action, status, FormCanvas.updateActions(self)
        if status is FAILURE:
            # Render correctly the validation errors
            for error in form.formErrors:
               self.send_message(error.title, type="error")
        SubFormGroupBase.updateWidgets(self)
        FormCanvas.updateWidgets(self)
        result = {'ifaces': ['form'],
                  'success': status == SUCCESS,
                  'forms': self.render()}
        portlets = queryMultiAdapter(
            (self.context, self.request, self), name='portlets')
        if portlets is not None:
            portlets.update()
            rendered_portlets = portlets.render().strip()
            if rendered_portlets:
                result['portlets'] = rendered_portlets
        return result


class SMIComposedFormTemplate(pt.PageTemplate):
    pt.view(SMIComposedForm)


class ComposedConfigurationForm(SMIComposedForm):
    grok.baseclass()
    grok.name('admin')
    grok.require('zope2.ViewManagementScreens')
    ignoreContent = False

    def get_menu_title(self):
        return self.label

    def get_menu_parent(self):
        parent = super(ComposedConfigurationForm, self).get_menu_parent()
        parent['screen'] = 'admin'
        return parent


class SMISubForm(SilvaFormData, composed.SubForm):
    """SMI Sub forms.
    """
    grok.baseclass()
    grok.implements(ISMIForm)

    dataValidators = [validation.InvariantsValidation]

    def get_content_path(self, content):
        return self.parent.get_content_path(content)


class SMISubEditForm(SMISubForm):
    grok.baseclass()
    grok.require('silva.ReadSilvaContent')

    dataManager = SilvaDataManager
    ignoreContent = False
    actions = Actions(
        CancelAction(),
        EditAction())

    def setContentData(self, content):
        """Set edited content. If the content is a versioned content,
        choose the correct version. This can change the form display
        mode, if the content is only previewable, or if you don't have
        the permission to edit it.
        """
        original = content
        if IVersionedObject.providedBy(original):
            content = original.get_editable()
            if content is None:
                self.widgetFactoryFactory = SMIDisplayWidgetFactory
                content = original.get_previewable()

        super(SMISubEditForm, self).setContentData(content)

    def update(self):
        # If you don't have the permission to edit the content, then
        # you don't. This can't be done in setContentData, as this is
        # called before security is verified.
        content = self.getContentData().content
        if not checkPermission('silva.ChangeSilvaContent', content):
            self.widgetFactoryFactory = SMIDisplayWidgetFactory


class SMISubFormTemplate(pt.PageTemplate):
    pt.view(SMISubForm)


class SMISubFormGroup(SilvaFormData, composed.SubFormGroup):
    """SMI sub form group.
    """
    grok.baseclass()

    def get_content_path(self, content):
        return self.parent.get_content_path(content)


class SMISubFormGroupTemplate(pt.PageTemplate):
    pt.view(SMISubFormGroup)


class SMISubTableForm(SilvaFormData, table.SubTableForm):
    """SMI Sub table forms.
    """
    grok.baseclass()
    grok.implements(ISMIForm)

    def get_content_path(self, content):
        return self.parent.get_content_path(content)


class SMISubTableFormTemplate(pt.PageTemplate):
    pt.view(SMISubTableForm)


class SMIAddForm(SMIForm):
    """ SMI add form
    """
    grok.baseclass()

    prefix = 'addform'

    fields = Fields(ITitledContent)
    ignoreContent = True
    actions = Actions(CancelAddAction())

    @property
    def label(self):
        return _('Add a ${content_type}',
            mapping={'content_type': self._content_type})

    @property
    def _content_type(self):
        return self.__name__.split('/')[0]

    def _add(self, parent, data):
        """Purely create the object. This method can be overriden to
        support custom creation needs.
        """
        # Search for an addable and a factory
        addable = extensionRegistry.get_addable(self._content_type)
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
        _(u'Save'),
        description=_(u"Create a new content"),
        factory=ExtractedDecoratedAction,
        implements=IDefaultAction,
        accesskey=u'ctrl+s')
    def save(self, data):
        try:
            content = self._add(self.context, data)
        except ValueError, error:
            self.send_message(error.args[0], type=u"error")
            return FAILURE
        self.send_message(
            _(u'Added ${meta_type}.', mapping={'meta_type': self._content_type}),
            type="feedback")
        raise RedirectToPage(content)



class SMIEditForm(SMIForm):
    """SMI Edit form.
    """
    grok.baseclass()
    # The permission is read. If the user doesn't have the right to
    # change the content, the form mode will be switch to display
    # mode.
    grok.require('silva.ReadSilvaContent')

    prefix = 'editform'

    dataManager = SilvaDataManager
    ignoreContent = False
    actions = Actions(
        CancelEditAction(),
        EditAction())

    @property
    def label(self):
        return _('Edit a ${content_type}',
            mapping={'content_type': self.context.meta_type})

    def setContentData(self, content):
        """Set edited content. If the content is a versioned content,
        choose the correct version. This can change the form display
        mode, if the content is only previewable, or if you don't have
        the permission to edit it.
        """
        original = content
        if IVersionedObject.providedBy(original):
            content = original.get_editable()
            if content is None:
                self.widgetFactoryFactory = SMIDisplayWidgetFactory
                content = original.get_previewable()

        super(SMIEditForm, self).setContentData(content)

    def update(self):
        # If you don't have the permission to edit the content, then
        # you don't. This can't be done in setContentData, as this is
        # called before security is verified.
        content = self.getContentData().content
        if not checkPermission('silva.ChangeSilvaContent', content):
            self.widgetFactoryFactory = SMIDisplayWidgetFactory

