#!/bin/bash

# Create directories with correct permissions for ssh client
SSH_DIR=/home/postgres/.ssh
mkdir $SSH_DIR
chmod 700 $SSH_DIR

if [ -d /ssh_keys ]; then
   cp /ssh_keys/* $SSH_DIR
fi


if [ -f $SSH_DIR/config ]; then
   chmod 644  $SSH_DIR/id_rsa.pub
fi

if [ -f $SSH_DIR/id_rsa.pub ]; then
   chmod 644  $SSH_DIR/id_rsa.pub
fi

if [ -f $SSH_DIR/id_rsa ]; then
   chmod 600  $SSH_DIR/id_rsa
fi

if [ "$START_SSHD" = true ]; then

   SSH_CONF=/ssh_conf_template
   
   mkdir /home/postgres/sshd
   
   # Generate server keys if not existing
   if [ ! -f $SSH_CONF/ssh_host_ecdsa_key ]; then
      echo "Host key $SSH_CONF/ssh_host_ecdsa_key not found - generating a new one"
      ssh-keygen -q -N "" -t ecdsa -f $SSH_CONF/ssh_host_ecdsa_key
   fi
   if [ ! -f $SSH_CONF/ssh_host_ed25519_key ]; then
      echo "Host key $SSH_CONF/ssh_host_ed25519_key not found - generating a new one"
      ssh-keygen -q -N "" -t ed25519 -f $SSH_CONF/ssh_host_ed25519_key
   fi
   if [ ! -f $SSH_CONF/ssh_host_rsa_key ]; then
      echo "Host key $SSH_CONF/ssh_host_rsa_key not found - generating a new one"
      ssh-keygen -q -N "" -t rsa -f $SSH_CONF/ssh_host_rsa_key
   fi
#
   # Copy the keys and the config to the home directory  
   cp -r $SSH_CONF/* /home/postgres/sshd/

   # Copy authorized keys
   if [ -f $SSH_DIR/authorized_keys ]; then
      chmod 600  $SSH_DIR/authorized_keys
   fi

   chmod 600 /home/postgres/sshd/ssh_host*

   /usr/sbin/sshd -f /home/postgres/sshd/sshd_config

fi
