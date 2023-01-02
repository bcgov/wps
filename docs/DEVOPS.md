## Reverting Deployment

To redeploy prod from a previous image:

1. Find the previous working image in openshift and run
   - `oc -n e1e498-tools tag wps-prod:pr-<last-working-pr-number> wps-prod:prod`
2. Select "Start rollout" action in openshift

### Disk space

A subset of model predictions is currently being stored, but not actually used once interpolation has been
performed. This data can be trimmed in order to preserve space:

```sql
delete from model_run_grid_subset_predictions where prediction_timestamp < now() - interval '3 months'
```

## Config Maps & Secrets

In `openshift/templates/global.config.yaml` there are templates for a global ConfigMap and global Secrets used by the API.
These templates can be applied to the Openshift project from the command line. For example, to apply the global.config template and pass a value for the WFWX-AUTH-URL parameter, run

`oc -n <openshift-project-name> process -f openshift/templates/global.config.yaml -p WFWX-AUTH-URL=https://spotwx.com/ | oc create -f -`

## Increasing Database Disk Space in Openshift

These are the steps necessary to increase the amount of disk space provisioned for the database hosted in **Openshift 3**:

### The easy way

1. Go to Storage -> Actions -> Expand PVC. Enter the desired size and click on expand.

2. That's it. No pod restarts required, the pods should pick up the increased size after a while.

### The hard way

1. From the Storage tab in the Openshift Cluster Console, delete the PVC of one of the Patroni replicas (note: a secondary replica, NOT the leader). Make a note of the PVC's name before you delete it.
2. From the Openshift Application Console, delete the pod associated with the PVC you just deleted. A new pod of the same name will immediately be recreated, but will not have any PVC to bind to yet. This is fine.
3. From the Openshift Cluster Console, create a new PVC.
   - the new PVC must have the same name as the PVC that was deleted in Step 1
   - set the requested storage to the desired size in Gi (GB)
   - delete all the labels that are set as defaults under the `selector` section in the YAML file. The PVC will fail to create and will be indefinitely stuck in the `Pending` state if there are any labels attached to the PVC
   - change the value of `storageClassName` from the default `slow` to `netapp-file-standard`. The `slow` storage class is not available in BCGov's incarnation of Openshift, so the PVC will be indefinitely stuck in the `Pending` state if the slow storage class is used.
   - click Create at the bottom of the screen
4. Once the newly created PVC has been initialized, the new pod from Step 2 will automatically bind to the new PVC. Resynchronization of the database on this pod will begin automatically.
5. Wait until the pod from Step 4 is Running and Ready (from the Application Console), then repeat the process with the other Patroni replica(s).
6. Perform steps 1-4 on the Patroni leader **last**.
