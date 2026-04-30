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
