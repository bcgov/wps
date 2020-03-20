FROM ashtonmeuser/openshift-cli:latest

RUN apk add git make

COPY . .

ENTRYPOINT ["/entrypoint.sh"]
