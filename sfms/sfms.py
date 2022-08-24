"""
Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.


This script is used to upload SFMS output to the Predictive Services Unit API.

The code relating to multipart form data is based on the blog post:
https://blog.thesparktree.com/the-unfortunately-long-story-dealing-with

The code could have been simplified by using the requests library, BUT: "Python 2.7 reached the 
end of its life on January 1st, 2020. Please upgrade your Python as Python 2.7 is no longer 
maintained. pip 21.0 will drop support for Python 2.7 in January 2021." - so it's best to avoid
any external dependencies.
"""
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
    file = None
    try:
        file = open(ini, 'r')
        config = {}
        for line in file.readlines():
            line = line.strip()
            if line.startswith('#'):
                continue
            if line:
                key, value = line.split('=')
                config[key] = value
    finally:
        if file:
            file.close()
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


def upload(filename, url, secret, last_modified, create_time):
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
                logger.info('Uploading "%s"', filename)
                upload(filename, config.get('url'), config.get('secret'), last_modified, create_time)
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
