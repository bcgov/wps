#!/usr/bin/env bash

## Installs and configures lima for docker via brew

brew install lima

limactl start --name=default template://docker