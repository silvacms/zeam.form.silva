# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from Acquisition import aq_base
from persistent.interfaces import IPersistent

from zope.interface import Interface
from zeam.form.base.datamanager import ObjectDataManager
from zeam.form.base.datamanager import BaseDataManager
from zeam.form.base.interfaces import IFields
from zeam.form.silva import interfaces
from zeam import component

_marker = object()


class SilvaDataManager(ObjectDataManager):
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


class FieldValueWriter(component.Component):
    """Write a Formulator field data on an object.
    """
    component.provides(interfaces.IFieldValueWriter)
    component.implements(interfaces.IFieldValueWriter)
    component.adapts(IPersistent, Interface)

    def __init__(self, identifier, field, content, form):
        self.identifier = identifier
        self.field = field
        self.form = form
        self.content = content

    def delete(self):
        if self.identifier in self.content.__dict__:
            del self.content.__dict__[self.identifier]
            self.content._p_changed = True

    def __call__(self, value):
        self.content.__dict__[self.identifier] = value
        self.content._p_changed = True


class FieldValueReader(component.Component):
    """Read a Formulator field data from an object.
    """
    component.provides(interfaces.IFieldValueReader)
    component.implements(interfaces.IFieldValueReader)
    component.adapts(Interface, Interface)

    def __init__(self, identifier, field, content, form):
        self.identifier = identifier
        self.field = field
        self.content = content
        self.form = form

    def __call__(self, default=None):
        return self.content.__dict__.get(self.identifier, default)


class FieldValueDataManager(BaseDataManager):
    """A data manager that adapt each of the fields separatly in
    order to set or get its value.
    """

    def __init__(self, form, content):
        self.form = form
        self.content = content
        self._readers = {}
        self._writers = {}

    def _get(self, identifier, cache, iface):
        field = self.form.fields[identifier]
        factory = cache.get(identifier, _marker)
        if factory is _marker:
            factory = component.getComponent(
                (self.form.fields[identifier], self.form), provided=iface)
            cache[identifier] = factory
        return factory(identifier, field, self.content, self.form)

    def get(self, identifier):
        reader = self._get(
            identifier, self._readers, interfaces.IFieldValueReader)
        value = reader(default=_marker)
        if value is _marker:
            raise KeyError(identifier)
        return value

    def set(self, identifier, value):
        writer = self._get(
            identifier, self._writers, interfaces.IFieldValueWriter)
        writer(value)

    def delete(self, identifier):
        writer = self._get(
            identifier, self._writers, interfaces.IFieldValueWriter)
        writer.delete()


def FieldValueDataManagerFactory(self, content):
    return FieldValueDataManager(self, content)


class MultiDataManager(BaseDataManager):

    def __init__(self, configuration, content):
        self._managers = managers = {}
        for field, factory in configuration:
            manager = factory(content)
            if isinstance(field, basestring):
                managers[field] = manager
            elif IFields.providedBy(field):
                for unique_field in field:
                    manager[unique_field.identifier] = manager
            elif field is None:
                if None in managers:
                    raise ValueError('More than one default manager')
                managers[None] = manager
        self.content = content

    def get(self, identifier):
        manager = self._managers.get(identifier)
        if manager is None:
            manager = self._managers[None]
        return manager.get(identifier)

    def set(self, identifier, value):
        manager = self._managers.get(identifier)
        if manager is None:
            manager = self._managers[None]
        manager.set(identifier, value)

    def delete(self, identifier):
        manager = self._managers.get(identifier)
        if manager is None:
            manager = self._managers[None]
        manager.delete(identifier)


def MultiDataManagerFactory(configuration):

    def Factory(content):
        return MultiDataManager(configuration, content)

    return Factory
