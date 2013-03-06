# -*- coding: utf-8 -*-
# Copyright (c) 2010-2013 Infrae. All rights reserved.
# See also LICENSE.txt

from five import grok
from zope.component import getUtility

from zeam.form.silva.interfaces import ISilvaFormData
from silva.core.messages.interfaces import IMessageService


class SilvaFormData(object):
    grok.implements(ISilvaFormData)

    def send_message(self, message, type=u""):
        service = getUtility(IMessageService)
        service.send(message, self.request, namespace=type)


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
