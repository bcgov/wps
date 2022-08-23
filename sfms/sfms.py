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
"""
import sys
import os
import mimetools
import mimetypes
import io
import httplib
import urlparse
import codecs


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
        return

    def get_content_type(self):
        return 'multipart/form-data; boundary=%s' % self.boundary

    def add_field(self, name, value):
        """Add a simple field to the form data."""
        self.form_fields.append((name, value))
        return

    def add_file(self, fieldname, filename, mimetype=None):
        """Add a file to be uploaded."""
        fileHandle = None
        try:
            fileHandle = codecs.open(filename, "rb")
            body = fileHandle.read()
        finally:
            if fileHandle:
                fileHandle.close()
        basename = os.path.basename(filename)
        if mimetype is None:
            mimetype = mimetypes.guess_type(basename)[0] or 'application/octet-stream'
        self.files.append((fieldname, basename, mimetype, body))
        return

    def get_binary(self):
        """Return a binary buffer containing the form data, including attached files."""
        part_boundary = '--' + self.boundary

        binary = io.BytesIO()
        needsCLRF = False
        # Add the form fields
        for name, value in self.form_fields:
            if needsCLRF:
                binary.write('\r\n')
            needsCLRF = True

            block = [part_boundary,
                     'Content-Disposition: form-data; name="%s"' % name,
                     '',
                     value
                     ]
            binary.write('\r\n'.join(block))

        # Add the files to upload
        for field_name, filename, content_type, body in self.files:
            if needsCLRF:
                binary.write('\r\n')
            needsCLRF = True

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


def upload(filename, url, secret):
    """ Give a filename, URL and secret, post file to the url.

    Based on blogpost: https://blog.thesparktree.com/the-unfortunately-long-story-dealing-with
    """
    form = MultiPartForm()
    form.add_file('file', filename)
    form_buffer = form.get_binary().getvalue()

    schema, netloc, url, params, query, fragments = urlparse.urlparse(url)
    http = httplib.HTTPConnection(netloc)
    http.connect()
    http.putrequest('POST', url)
    http.putheader('Secret', secret)
    http.putheader('Content-type', form.get_content_type())
    http.putheader('Content-length', str(len(form_buffer)))
    http.endheaders()
    http.send(form_buffer)
    result = http.getresponse()

    print('Status: ' + str(result.status))


def main(ini):
    """ Given some configuration filename, POST all files to the confured URL. """
    config = get_config(ini)
    print('Uploading tiff files from "' + config.get('source') + '" to "' + config.get('url') + '"')

    # Iterate over all files in the directory
    for filename in os.listdir(config.get('source')):
        filename = filename.lower()
        if filename.endswith('tif') or filename.endswith('tiff'):
            filename = os.path.join(config.get('source'), filename)
            try:
                print('Uploading: ' + filename)
                upload(filename, config.get('url'), config.get('secret'))
            except KeyboardInterrupt:
                print('Aborted')
                sys.exit(1)
            except:
                print('Error uploading: ' + filename)
                print(sys.exc_info()[0])


if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: python sfms.py <ini file>')
        sys.exit(1)
    main(sys.argv[1])
