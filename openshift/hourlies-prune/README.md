# Hourlies Prune Job

Deletes hourlies from object that are from the day before yesterday, to maintain the last 24 hours of hourly FFMC tifs.

## Building

### Apply template to build the base image on Openshift

```bash
oc -n e1e498-tools process -f build.yaml | oc -n e1e498-tools apply -f -
```

### Apply template using a specified branch and version

```bash
oc -n e1e498-tools process -p VERSION=some-date -p GIT_BRANCH=my-branch process -f build.yaml | oc -n e1e498-tools apply -f -
```

### Kick off the build

```bash
oc -n e1e498-tools start-build hourlies-prune --follow
```

### Re-tag for production

Assuming you've built an image tagged for dev, you may now want to tag it for production. Remember to retain
the current prod image in case you want to revert!

You may also want to delete any old tags that are no longer relevant.

```bash
# maybe tag the current production image in case we need to revert
oc -n e1e498-tools tag hourlies-prune:prod hourlies-prune:previous-prod
# tag this image with something useful, may todays date
oc -n e1e498-tools tag hourlies-prune:dev hourlies-prune:some-sensible-tag-like-the-current-date
# tag it for production
oc -n e1e498-tools tag hourlies-prune:dev hourlies-prune:prod
```
