# unicorn base image

The Docker image and template in this folder are used to create the base image used in the api build.

- Using this base image can save some time, as it installs some ubuntu packages that can time some time.
- Using this base image reduces how often we have to pull the upstream image from docker.

## apply template

```bash
oc -n e1e498-tools process -f build.yaml | oc -n e1e498-tools apply -f -
```

## apply template using a specified branch

```bash
oc -n e1e498-tools -p GIT_BRANCH=my-branch process -f build.yaml | oc -n e1e498-tools apply -f -
```
