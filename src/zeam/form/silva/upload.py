import logging
import json
from five import grok
from infrae import rest

from silva.core.interfaces import ISilvaObject

logger = logging.getLogger('silva.upload')


class Upload(rest.REST):
    """ Check security and return information about gp.fileupload upload
    """
    grok.context(ISilvaObject)
    grok.require('silva.ChangeSilvaContent')
    grok.name('upload')

    def POST(self):
        """ get information about file upload
        """
        upload_id = long(self.request.get('gp.fileupload.id'))
        paths = self.request.environ.get('HTTP_STORED_PATHS', '').split(':')
        path = paths[0]
        logger.info("upload paths: %r" % paths)
        return """
            <html>
                <body>
                    <script>
                        var $ = window.parent.jQuery;
                        $(window.parent.document).trigger('done.%d.upload', %s);
                    </script>
                </body>
            </html>
        """ % (upload_id, json.dumps({'path': path, 'upload-id': upload_id}))
