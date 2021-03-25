#!/usr/bin/env bash

: "${CERTBOT_CONFIG_DIR:=/etc/letsencrypt}"
: "${CERTBOT_LOGS_DIR:=/var/log/letsencrypt}"
: "${CERTBOT_WORK_DIR:=/var/lib/letsencrypt}"
: "${CERTBOT_DEPLOY_DIR:=/etc/letsencrypt/renewal-hooks/deploy}"
: "${CERTBOT_RSA_KEY_SIZE:=2048}"
: "${CERTBOT_DELETE_ACME_ROUTES:=true}"
: "${CERTBOT_DEBUG:=false}"
: "${CERTBOT_STAGING:=false}"
: "${CERTBOT_DRY_RUN:=false}"

if [ -z "$CERTBOT_EMAIL" ]; then echo "Missing 'CERTBOT_EMAIL' environment variable" && exit 1; fi

mkdir -p "$CERTBOT_CONFIG_DIR" "$CERTBOT_WORK_DIR" "$CERTBOT_LOGS_DIR" "$CERTBOT_DEPLOY_DIR"

cat > /tmp/certbot.ini <<EOF
rsa-key-size = $CERTBOT_RSA_KEY_SIZE
authenticator = standalone
http-01-port = 8080
https-port = 4443
preferred-challenges = http
agree-tos = true
email = $CERTBOT_EMAIL

config-dir = $CERTBOT_CONFIG_DIR
work-dir = $CERTBOT_WORK_DIR
logs-dir = $CERTBOT_LOGS_DIR
EOF

if [ "${CERTBOT_STAGING}" == "true" ]; then
  echo "staging = true" >> /tmp/certbot.ini
fi

cat > $CERTBOT_CONFIG_DIR/renewal-hooks/deploy/set-deployed-flag.sh << EOF
#!/bin/sh
touch $CERTBOT_WORK_DIR/deployed
EOF
chmod +x $CERTBOT_CONFIG_DIR/renewal-hooks/deploy/set-deployed-flag.sh

cat > /tmp/certbot-svc.yaml <<'EOF'
apiVersion: v1
kind: Service
metadata:
  creationTimestamp: null
  labels:
    app: certbot
    well-known: acme-challenge
  name: certbot
spec:
  ports:
    - name: http
      port: 8080
      protocol: TCP
      targetPort: 8080
  selector:
    app: certbot
  sessionAffinity: None
  type: ClusterIP
EOF

cat > /tmp/certbot-route.yaml <<'EOF'
apiVersion: v1
kind: Template
metadata:
  creationTimestamp: null
  name: certbot-well-known
parameters:
- name: NAME
- name: HOST
objects:
- apiVersion: route.openshift.io/v1
  kind: Route
  metadata:
    annotations:
      haproxy.router.openshift.io/timeout: 5m
    labels:
      app: certbot
      well-known: acme-challenge
    name: ${NAME}
  spec:
    host: ${HOST}
    path: /.well-known/acme-challenge/
    port:
      targetPort: http
    tls:
      insecureEdgeTerminationPolicy: Allow
      termination: edge
    to:
      kind: Service
      name: certbot
      weight: 100
    wildcardPolicy: None
EOF

#Prepare list of domains
oc get route -l certbot-managed=true -o json | jq '.items[].spec.host' -r | sort -f | uniq -iu > /tmp/certbot-hosts.txt
cat /tmp/certbot-hosts.txt | paste -sd "," - > /tmp/certbot-hosts.csv

echo 'CERTBOT_DEBUG =' $CERTBOT_DEBUG
# Dump contents of files to help troubleshoot in case of problems
if [ "${CERTBOT_DEBUG}" == "true" ]; then
  echo '*********** contents of /tmp/certbot-hosts.csv:'
  cat /tmp/certbot-hosts.csv

  echo '*********** contents of /tmp/certbot-hosts.txt:'
  cat /tmp/certbot-hosts.txt

  echo '*********** contents of /tmp/certbot-route.yaml:'
  cat /tmp/certbot-route.yaml

  echo '*********** contents of /tmp/certbot-svc.yaml:'
  cat /tmp/certbot-svc.yaml

  echo '*********** contents of /tmp/certbot.ini:'
  cat /tmp/certbot.ini
fi

#List of Routes
oc get route -l certbot-managed=true -o json | jq '.items[].metadata.name' -r > /tmp/certbot-routes.txt

# Delete well-known/acme-challenge routes
oc delete route,svc -l app=certbot,well-known=acme-challenge

# Create certbot service
oc create -f /tmp/certbot-svc.yaml

#Create well-known/acme-challenge routes
cat /tmp/certbot-hosts.txt | xargs -n 1 -I {} oc process -f /tmp/certbot-route.yaml -p 'NAME=acme-challenge-{}' -p 'HOST={}' | oc create -f -

# Sleep for 5sec. There was an issue noticed where the pod wasn't able to get a route and was giving 404 error. Not totally certain if this helps.
sleep 5s

rm -f $CERTBOT_WORK_DIR/deployed
CERTBOT_ARGS='--no-random-sleep --no-eff-email'
if [ "${CERTBOT_DRY_RUN}" == "true" ]; then
  CERTBOT_ARGS="${CERTBOT_ARGS} --dry-run"
fi

if [ "${CERTBOT_DEBUG}" == "true" ]; then
  CERTBOT_ARGS="${CERTBOT_ARGS} --debug"
fi

if [ ! -z "$CERTBOT_SERVER" ]; then
  CERTBOT_ARGS="${CERTBOT_ARGS} --server ${CERTBOT_SERVER}"
fi

set -x
# if there is no certificate issue, request a new one
if [ ! -f "${CERTBOT_CONFIG_DIR}/live/openshift-route-certs/cert.pem" ]; then
  certbot --config /tmp/certbot.ini certonly $CERTBOT_ARGS --non-interactive --keep-until-expiring --cert-name 'openshift-route-certs' --expand --standalone -d "$(</tmp/certbot-hosts.csv)"
else
  # if a certificate already exists, request to renew it
  certbot --config /tmp/certbot.ini renew $CERTBOT_ARGS --no-random-sleep-on-renew --cert-name 'openshift-route-certs'
fi
set +x

if [ "${CERTBOT_DRY_RUN}" == "true" ]; then
  exit 0
fi

if [ -f $CERTBOT_WORK_DIR/deployed ]; then
  echo 'New certificate(s) have been issued'
else
  echo 'NO certificate(s) have been issued'
fi

#if [ -f $CERTBOT_WORK_DIR/deployed ]; then
echo 'Updating Routes'
CERTIFICATE="$(awk '{printf "%s\\n", $0}' $CERTBOT_CONFIG_DIR/live/openshift-route-certs/cert.pem)"
KEY="$(awk '{printf "%s\\n", $0}' $CERTBOT_CONFIG_DIR/live/openshift-route-certs/privkey.pem)"
CABUNDLE=$(awk '{printf "%s\\n", $0}' $CERTBOT_CONFIG_DIR/live/openshift-route-certs/fullchain.pem)

# If any of the cert components is blank, then don't run the patch command
if [ "${CERTIFICATE}" == "" ] || [ "${KEY}" == "" ] || [ "${CABUNDLE}" == "" ]; then
  echo "Certs weren't created properly and no routes were patched."
else
  cat /tmp/certbot-routes.txt | xargs -n 1 -I {} oc patch "route/{}" -p '{"spec":{"tls":{"certificate":"'"${CERTIFICATE}"'","key":"'"${KEY}"'","caCertificate":"'"${CABUNDLE}"'"}}}'
fi

# Print the log file if debugging is enabled
if [ "${CERTBOT_DEBUG}" == "true" ]; then
  echo '*********** list of all files/folder under /etc/letsencrypt:'
  find /etc/letsencrypt

  echo '*********** list of all files/folder under /var/log/letsencrypt:'
  find /var/log/letsencrypt

  echo '*********** list of all files/folder under /var/lib/letsencrypt:'
  find /var/lib/letsencrypt

  echo '*********** contents of /var/log/letsencrypt/letsencrypt.log:'
  cat /var/log/letsencrypt/letsencrypt.log

  echo '*********** contents of /etc/letsencrypt/renewal/openshift-route-certs.conf:'
  cat /etc/letsencrypt/renewal/openshift-route-certs.conf
fi

if [ "${CERTBOT_DELETE_ACME_ROUTES}" == "true" ]; then
  # Delete well-known/acme-challenge routes
  echo "Deleting ACME service and routes"
  oc delete route,svc -l app=certbot,well-known=acme-challenge
else
  echo "ACME service and routes were not deleted, please clean them up manually."  
fi
