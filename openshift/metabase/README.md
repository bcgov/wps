# Metabase

Metabase is an open-source tool that provides a GUI over top of existing databases. It allows authenticated users to view tables, query data, create and share data dashboards, save data queries, and more.

## Reference

[NR Showcase Devops's](https://github.com/bcgov/nr-showcase-devops-tools/tree/master/tools/metabase) Github repo was extensively used to integrate Metabase into this project. All Metabase scripts in this repo are based on their examples and documentation.

## To Use

To deploy Metabase manually into an Openshift environment,

1. Authenticate into your Openshift project using Openshift's CLI.
2. Run the `oc_build_metabase.sh` script in this folder, updating the exported variables as needed.
3. Run the `oc_deploy_metabase.sh` script in this folder, updating the exported variables as needed.
4. (Optional) If your Metabase instance is located in a different namespace than the database you want to connect to, run the `oc_network_policy_metabase.sh` script in this folder to create a network policy that will allow connections between the two Openshift namespaces.

## Configuring Database Connection

The Metabase instance's connection to the database is configured manually through the Metabase admin panel.

## Configuring LDAP authentication

Metabase requires user authentication, and by default will require that users create a Metabase account in order to access the instance.
Alternatively, users can use their government-issued IDIR account to authenticate into Metabase. To permit this, you must configure LDAP authentication into your Metabase instance by following [these instructions](https://apps.nrs.gov.bc.ca/int/confluence/display/OPTIMIZE/LDAP+Integration)

## Updating the version of Metabase

Refer to [this Confluence page](https://apps.nrs.gov.bc.ca/int/confluence/display/OPTIMIZE/Updating+Metabase) for instructions on how to update the version of Metabase you're using.

