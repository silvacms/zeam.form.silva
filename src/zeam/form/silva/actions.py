from zope.configuration.name import resolve

from silva.core.interfaces import IRoot
from silva.core.conf.utils import getFactoryName

from zeam.form.silva.interfaces import IDefaultAddFields
from zeam.form.base.actions import Action
from zeam.form.base import FAILURE

from Products.Silva.ExtensionRegistry import extensionRegistry


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
        editable_obj = obj.get_editable()
        for key, value in data.iteritems():
            if key not in IDefaultAddFields:
                setattr(editable_obj, key, value)
        return obj

    def __call__(self, form):
        data, errors = form.extractData()
        if form.errors:
            return FAILURE
        obj = self.add(form.context, data, form)
        form.setContentData(obj)
        form.redirect(self.nextURL(form, obj))

    def nextURL(self, form, content):
        return '%s/edit' % content.aq_inner.aq_parent.absolute_url()


class AddAndEditAction(AddAction):

    def nextURL(self, form, content):
        return '%s/edit' % content.absolute_url()


class CancelAddAction(Action):
    def __call__(self, form):
        return form.redirect(form.url(name="edit"))


class CancelEditAction(Action):

    def __call__(self, form):
        content = form.context
        if not IRoot.providedBy(form.context):
            content = form.context.aq_inner.aq_parent
        return form.redirect(form.url(obj=content, name='edit'))


