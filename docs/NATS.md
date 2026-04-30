# NATS on OpenShift

This is a quick guide for checking and fixing JetStream consumer config in OpenShift.

## What Persists

- The NATS server config comes from a `ConfigMap`.
- JetStream stream and durable consumer state is persisted on the NATS PVC
- Because of that, changing app code or the `ConfigMap` does not automatically replace an existing durable consumer config.

The durable consumer we care about is `hfi_classify`.

## Check and Fix Config (if change needed)

### 1. Check existing config

First, login to the openshift cli and start a temporary NATS toolbox pod

```bash
oc -n <namespace> run nats-box --rm -it --restart=Never --image=natsio/nats-box -- sh
```

Then check config with:

```bash
nats --server nats://consumer:consumer@wps-prod-nats:4222 consumer info wps-prodsfms hfi_classify
```

Look for:

- `Maximum Deliveries`
- `Ack Wait`
- `Ack Policy`

Or anything else that should be changed in the config

### 4. Delete the durable consumer so the app can recreate it

Scale the NATS consumer pods down to 0.

Inside the toolbox shell:

```bash
nats --server nats://consumer:consumer@wps-prod-nats:4222 consumer rm wps-prodsfms hfi_classify
```

### 5. Scale the consumer deployment back up

Scale the pods back up with UI or CLI.

### 6. Verify the recreated consumer config

```bash
nats --server nats://consumer:consumer@wps-prod-nats:4222 consumer info wps-prodsfms hfi_classify
```

Confirm the server-side values match the current app config.

Exiting the `nats-box` terminal should delete the pod, if not delete it manually.

---

# Running NATS Locally

### Requirements for running nats locally

- You have run the [lima setup steps](../setup/LIMA.md)
- You are able to run the sfms script locally so you can upload tiffs for testing

### Steps for running nats locally

##### 1. Check if you have a default VM running already:

```bash
limactl list
```

You should see a default with STATUS=Running

_a. If there is no default VM_

```bash
limactl start --name=default template://docker
```

_b. If there is a default VM but it is not running_

```bash
limactl start default
```

##### 2. Spin up a nats server:

```bash
lima nerdctl run -p 4222:4222 -ti nats:latest -js
```

##### 3. Open up a new terminal and run the api:

```bash
cd {path_to_repo}/wps/api
make run
```

##### 4. Run the nats consumer from VS Code, click the debug button on the sidebar, choose the 'nats' option from the drop-down and click the play button.

nats should now be fully up and running. You should be able to run sfms and upload a tiff.

## Common Problems

1. You see '**main** - ERROR - There was an error:' in the VS Code terminal after starting nats. This is probably a TimeoutError from asyncio due to the nats consumer being unable to connect to the nats server running in the container. Stop the nats server (Ctrl + C), restart the lima VM and start the nats server again:

```bash
limactl stop default
limactl start default
lima nerdctl run -p 4222:4222 -ti nats:latest -js
```
