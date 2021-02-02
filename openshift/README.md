# Openshift

## Templates - Tools

### Network Security Policy

In order for build configs to work, you'll need to apply a network security policy that allows egress to the internet:

```bash
oc -n e1e498-tools process -f templates/tools.nsp.yaml | oc apply -f -
```

### Jenkins

Refer to https://developer.gov.bc.ca/Migrating-Your-BC-Gov-Jenkins-to-the-Cloud

- Build the basic Jenkins image. See: https://developer.gov.bc.ca/Migrating-Your-BC-Gov-Jenkins-to-the-Cloud#building-the-jenkins-image

- Create a primary jenkins server: `oc process -f jenkins.dc.yaml | oc apply -f -`
- Create a secondary jenkins server: `oc process -f jenkins-secondary.dc.yaml | oc apply -f -`
- Add GitHub credentials to Jenkins. Use type username/password, with a GitHub token as the password. The bcgov-csnr-cd account can be used.

- Add multibranch pipeline
- Discover pull requests from origing -> Merging the pull request with the current branch revision.
- Disover pull requests from forks -> Remove, we don't do forks.

#### Known issues

- If the Jenkins secondary binds to the PVC's before the primary, the primary is
  unable to start up, as it requires to be bound 1st. If this happens, pause deployments
  of the secondary and wait for the primary to start up.
