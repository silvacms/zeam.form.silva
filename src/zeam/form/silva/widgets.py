
from ZPublisher.HTTPRequest import FileUpload

from five import grok
from zope.interface import Interface

from silva.core.conf import schema as silvaschema

from zeam.form.base.markers import DISPLAY, INPUT, NO_VALUE
from zeam.form.base.widgets import WidgetExtractor
from zeam.form.ztk.fields import SchemaField, SchemaFieldWidget
from zeam.form.ztk.fields import registerSchemaField


def register():
    registerSchemaField(FileSchemaField, silvaschema.IBytes)


class FileSchemaField(SchemaField):
    """Field to upload a file.
    """


class FileWidgetInput(SchemaFieldWidget):
    grok.adapts(FileSchemaField, Interface, Interface)
    grok.name(str(INPUT))

    def valueToUnicode(self, value):
        return u''


class FileWidgetExtractor(WidgetExtractor):
    grok.adapts(FileSchemaField, Interface, Interface)

    def extract(self):
        value = self.request.form.get(self.identifier, u'')
        if not isinstance(value, FileUpload) or not value:
            value = NO_VALUE
        return value, None
