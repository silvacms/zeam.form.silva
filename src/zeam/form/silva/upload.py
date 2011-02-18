import logging
import json
from five import grok
from infrae import rest

from silva.core.interfaces import IContainer

logger = logging.getLogger('silva.upload')


class Upload(rest.REST):
    """ Check security and return information about gp.fileupload upload
    """
    grok.context(IContainer)
    grok.require('silva.ChangeSilvaContent')
    grok.name('upload')

    def POST(self):
        """ get information about file upload
        """
        upload_id = self.request.get('gp.fileupload.id')
        paths = self.request.environ.get('HTTP_STORED_PATHS', '').split(':')
        logger.info("upload paths: %r" % paths)
        return """
            <html>
                <body>
                    <script>
                        var $ = window.parent.jQuery;
                        $(window.parent.document).trigger('upload-finished', %s);
                    </script>
                </body>
            </html>
        """ % json.dumps({'paths': paths, 'upload-id': upload_id})
