import sys
import os
import mimetools
import mimetypes
import io
import httplib
import urlparse
import codecs
import logging
from datetime import datetime

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def get_config(ini):
    """ Some very simple code for reading a config file into a dictionary. """
    ini_file = None
    try:
        ini_file = open(ini, 'r')
        config = {}
        for line in ini_file.readlines():
            line = line.strip()
            if line.startswith('#') or line.startswith(';'):
                continue
            if line:
                key, value = line.split('=')
                config[key] = value
    finally:
        if ini_file:
            ini_file.close()
    return config


class MultiPartForm(object):
    """ Accumulate the data to be used when posting a form.
    Based on blogpost: https://blog.thesparktree.com/the-unfortunately-long-story-dealing-with    
    """

    def __init__(self):
        self.form_fields = []
        self.files = []
        self.boundary = mimetools.choose_boundary()

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))

    def add_file(self, fieldname, filename, mimetype=None):
        """Add a file to be uploaded."""
        file_handle = None
        try:
            file_handle = codecs.open(filename, "rb")
            body = file_handle.read()
        finally:
            if file_handle:
                file_handle.close()
        basename = os.path.basename(filename)
        if mimetype is None:
            mimetype = mimetypes.guess_type(basename)[0] or 'application/octet-stream'
        self.files.append((fieldname, basename, mimetype, body))

    def get_binary(self):
        """Return a binary buffer containing the form data, including attached files."""
        part_boundary = '--' + self.boundary

        binary = io.BytesIO()
        needs_clrf = False
        # Add the form fields
        for name, value in self.form_fields:
            if needs_clrf:
                binary.write('\r\n')
            needs_clrf = True

            block = [part_boundary,
                     'Content-Disposition: form-data; name="%s"' % name,
                     '',
                     value
                     ]
            binary.write('\r\n'.join(block))

        # Add the files to upload
        for field_name, filename, content_type, body in self.files:
            if needs_clrf:
                binary.write('\r\n')
            needs_clrf = True

            block = [part_boundary,
                     str('Content-Disposition: file; name="%s"; filename="%s"' %
                         (field_name, filename)),
                     'Content-Type: %s' % content_type,
                     ''
                     ]
            binary.write('\r\n'.join(block))
            binary.write('\r\n')
            binary.write(body)

        # add closing boundary marker,
        binary.write('\r\n--' + self.boundary + '--\r\n')
        return binary


def upload(filename, url, secret, last_modified, create_time, forecast_or_actual, issue_date):
    """ Give a filename, URL and secret, post file to the url.

    Based on blogpost: https://blog.thesparktree.com/the-unfortunately-long-story-dealing-with
    """
    form = MultiPartForm()
    form.add_file('file', filename)
    form_buffer = form.get_binary().getvalue()

    schema, netloc, url, params, query, fragments = urlparse.urlparse(url)
    if schema == 'https':
        http = httplib.HTTPSConnection(netloc)
    else:
        http = httplib.HTTPConnection(netloc)
    http.connect()
    http.putrequest('POST', url)
    http.putheader('Secret', secret)
    http.putheader('ForecastOrActual', forecast_or_actual)
    http.putheader('IssueDate', issue_date)
    http.putheader('Create-time', create_time.isoformat())
    http.putheader('Last-modified', last_modified.isoformat())
    http.putheader('Content-type', form.get_content_type())
    http.putheader('Content-length', str(len(form_buffer)))
    http.endheaders()
    http.send(form_buffer)
    result = http.getresponse()

    logger.info('Status: %s', result.status)


def main(ini):
    """ Given some configuration filename, POST all files to the configured URL. """
    config = get_config(ini)
    logger.info('Uploading tiff files from "%s" to "%s"', config.get('source'), config.get('url'))

    # Iterate over all files in the directory
    for filename in os.listdir(config.get('source')):
        filename = filename.lower()
        if filename.endswith('tif') or filename.endswith('tiff'):
            filename = os.path.join(config.get('source'), filename)
            last_modified = datetime.fromtimestamp(os.path.getmtime(filename))
            create_time = datetime.fromtimestamp(os.path.getctime(filename))
            try:
                logger.info('Uploading "%s" to %s', filename, config.get('url'))
                upload(filename, config.get('url'), config.get('secret'),
                       last_modified, create_time, config.get('forecast_or_actual'), config.get('issue_date'))
            except KeyboardInterrupt:
                logger.warning('Aborted')
                sys.exit(1)
            except Exception as exception:
                logger.error('Error uploading "%s" with %s', filename, exception, exc_info=True)
                print(sys.exc_info()[0])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python sfms.py <ini file>')
        sys.exit(1)
    main(sys.argv[1])
