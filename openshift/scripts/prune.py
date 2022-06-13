import sys
import json

try:
    # read from stdin (we're expecting JSON from a "oc get is/blah --output=json")
    response = json.load(sys.stdin)
    # make a list of tags and dates
    tags = []
    for tag in response['status']['tags']:
        if tag['items']:
            tags.append({'tag': tag['tag'], 'created': tag['items'][0]['created']})
    # order ascending by date
    tags.sort(key=lambda x: x['created'])
    # now - we only want to keep the N most recent, so pop off the N most recent, the rest we'll delete
    tags = tags[:-5]
    # output the list of tags to stdout
    for tag in tags:
        print(tag['tag'])
except:
    # if we can't read the JSON, just exit with an error
    sys.exit(1)
