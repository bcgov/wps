# Openshift

## Templates - Tools

### Network Security Policy

In order for build configs to work, you'll need to apply a network security policy that allows egress to the internet:

```bash
oc -n e1e498-tools process -f templates/tools.nsp.yaml | oc apply -f -
```

### Jenkins

Refer to https://developer.gov.bc.ca/Cloud-Migration/Migrating-Your-BC-Gov-Jenkins-to-the-Cloud

- Build the basic Jenkins image. See: https://developer.gov.bc.ca/Cloud-Migration/Migrating-Your-BC-Gov-Jenkins-to-the-Cloud#building-the-jenkins-image

- Create a primary jenkins server: `oc process -f jenkins.dc.yaml | oc apply -f -`
