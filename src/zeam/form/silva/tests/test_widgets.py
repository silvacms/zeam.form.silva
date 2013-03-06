# -*- coding: utf-8 -*-
# Copyright (c) 2002-2013 Infrae. All rights reserved.
# See also LICENSE.txt

import unittest

from zope import component
from zope.interface import Interface
from infrae.wsgi.testing import TestRequest

from zeam.form.base.interfaces import IWidget
from zeam.form.base.form import Form

from silva.core.conf.schema import CropCoordinates
from zeam.form import silva as silvaforms
from ..widgets.cropping import CropImageInputWidget
from Products.Silva.testing import FunctionalLayer


class ICropFields(Interface):

    crop = CropCoordinates(title=u'crop', required=True)


class ICropFieldsNotRequired(Interface):

    crop = CropCoordinates(title=u'crop', required=False)


class FormWithCropField(Form):

    fields = silvaforms.Fields(ICropFieldsNotRequired)
    actions = silvaforms.Actions(silvaforms.Action('No Action'))


class FormWithCropFieldRequired(Form):

    fields = silvaforms.Fields(ICropFields)
    actions = silvaforms.Actions(silvaforms.Action('No Action'))


class CropWidgetTestCase(unittest.TestCase):

    layer = FunctionalLayer

    def setUp(self):
        self.root = self.layer.get_application()
        factory = self.root.manage_addProduct['Silva']
        with self.layer.open_fixture('photo.tif') as image:
            self.image_data = image.read()
            self.image_size = image.tell()
            image.seek(0, 0)

            factory.manage_addImage('test_image', u'Image élaboré', image)

        self.image = self.root._getOb('test_image')
        self.fields = silvaforms.Fields(ICropFields)

    def test_widget_is_found(self):
        crop_field = self.fields['crop']
        request = TestRequest()
        widget = component.getMultiAdapter(
            (crop_field, Form(self.image, request), request),
            IWidget, name=u'input')
        self.assertIsInstance(widget, CropImageInputWidget)
        widget.update()
        widget.render()

    def test_widget_data(self):
        form = FormWithCropField(object(), TestRequest())
        data, errors = form.extractData()
        self.assertEquals([], list(errors))

    def test_widget_data_required(self):
        form = FormWithCropFieldRequired(self.image, TestRequest())
        data, errors = form.extractData()
        self.assertEquals(silvaforms.NO_VALUE, data.get('crop'))
        self.assertEquals('Missing required value.',
            errors['form.field.crop'].title)

    def test_widget_data_validation_empty(self):
        form = FormWithCropField(
            self.image, TestRequest(form={'form.field.crop': u''}))
        data, errors = form.extractData()
        self.assertEquals('', data.get('crop'))
        self.assertEquals(None, errors.get('form.field.crop', None))

    def test_widget_invalid_data(self):
        form = FormWithCropField(
            self.image, TestRequest(form={'form.field.crop': u'123x123-12'}))
        data, errors = form.extractData()
        self.assertEquals(None, data.get('crop'))
        self.assertEquals(
            'Invalid crop coordinates.', errors['form.field.crop'].title)

    def test_widget_valid_data(self):
        form = FormWithCropField(
            self.image, TestRequest(
                form={'form.field.crop': u'123x123-12x123'}))
        data, errors = form.extractData()
        self.assertEquals('123x123-12x123', data.get('crop'))
        self.assertEquals(None, errors.get('form.field.crop', None))


def test_suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CropWidgetTestCase))
    return suite
