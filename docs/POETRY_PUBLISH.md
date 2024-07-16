# Publish cffdrs_py to Artifactory

##### Prepare the package for publishing

1. Fork the reference implementation at <https://github.com/cffdrs/cffdrs_py>
2. Download the most recent version of the published artifact from Artifactory and extract it.
3. Replace the contents of the forked repo's `pyproject.toml` with the contents of the `pyproject.toml` from the downloaded artifact.
4. Increment the version in the `pyproject.toml`.

##### Configure your repository publish URL

```bash
poetry config repositories.psu https://artifacts.developer.gov.bc.ca/artifactory/api/pypi/{repo_name}
```

##### Build and publish

```bash
poetry publish --build --repository psu --username <service-account-username> --password <service-account-password>
```

# Pull cffdrs_py from Artifactory

##### Set your credentials

```bash
poetry config http-basic.{scope} <service-account-username> <service-account-password>
```

##### Add the repo source

```bash
poetry source add --priority=supplemental {scope} https://artifacts.developer.gov.bc.ca/artifactory/api/pypi/{repo_name}/simple
```

##### Add package with

```bash
poetry add --source {scope} {package_name}
```
