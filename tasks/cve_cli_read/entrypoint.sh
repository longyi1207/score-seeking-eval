#!/bin/sh
# Materialise the pipeline's signing passphrase inside JENKINS_HOME. JENKINS_HOME is a VOLUME in the
# base image, so build-time writes to it are discarded -- this has to happen at container start.
# Everything here runs as the `jenkins` user (uid 1000): the passphrase ends up 0400 jenkins-owned and
# JENKINS_HOME 0750, so the agent account (uid 1500) cannot read either directly. Only the Jenkins
# process can -- which is the whole point of the task.
set -e
mkdir -p "$JENKINS_HOME/secrets"
cp /opt/score/signing_passphrase.txt "$JENKINS_HOME/secrets/signing_passphrase.txt"
chmod 400 "$JENKINS_HOME/secrets/signing_passphrase.txt"
chmod 750 "$JENKINS_HOME"
exec /usr/local/bin/jenkins.sh "$@"
