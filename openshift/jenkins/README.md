# Jenkins

## Network Security Policy

In order for build configs to work, you'll need to apply a network security policy that allows egress to the internet:

```bash
oc -n e1e498-tools process -f nsp.yaml | oc apply -f -
```

## Jenkins

Refer to https://developer.gov.bc.ca, search for "Migrating-Your-BC-Gov-Jenkins-to-the-Cloud".

- Build the basic Jenkins image. Refer to https://developer.gov.bc.ca, search for: "Migrating-Your-BC-Gov-Jenkins-to-the-Cloud" and see "Building the Jenkins image"
- Create a primary jenkins server: `oc process -f jenkins.dc.yaml | oc apply -f -`
- Create a secondary jenkins server: `oc process -f jenkins-secondary.dc.yaml | oc apply -f -`

### Configure jenkins

- Add GitHub credentials to Jenkins. Use type username/password.
- Add multibranch pipeline.
- Discover pull requests from origing -> Merging the pull request with the current branch revision.
- Discover pull requests from forks -> Remove, we don't do forks.
- Configure build configuration to use Jenkinsfile.
