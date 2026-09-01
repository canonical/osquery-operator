#!/usr/bin/env bash
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.
#
# Provision the throwaway osctrl stack inside the LXD VM. Idempotent: installs
# Docker if missing, generates a self-signed TLS certificate for the controller
# hostname (with the VM's current IP in the SAN), then brings the compose stack
# up and waits until the osquery TLS endpoint and the API are both answering.
#
# Usage: provision.sh <controller-hostname>
set -euo pipefail

HOST="${1:?usage: provision.sh <controller-hostname>}"
cd "$(dirname "$0")"

echo "== Ensuring Docker is installed =="
if ! command -v docker >/dev/null 2>&1; then
    export DEBIAN_FRONTEND=noninteractive
    apt-get update -q
    apt-get install -y -q docker.io docker-compose-v2 openssl
fi
systemctl enable --now docker >/dev/null 2>&1 || true

echo "== Generating TLS certificate for ${HOST} =="
mkdir -p certs
IP="$(hostname -I | awk '{print $1}')"
openssl req -x509 -newkey rsa:2048 -nodes -days 3 \
    -keyout certs/osctrl.key -out certs/osctrl.crt \
    -subj "/CN=${HOST}" \
    -addext "subjectAltName=DNS:${HOST},IP:${IP}"

echo "== Pulling and starting the osctrl stack =="
docker compose pull -q
docker compose up -d

echo "== Waiting for the osctrl TLS endpoint to answer =="
deadline=$(( $(date +%s) + 300 ))
while true; do
    # curl always prints the code via -w; on connection failure that is 000.
    tls_code="$(curl -sk -o /dev/null -w '%{http_code}' "https://localhost/" 2>/dev/null || true)"
    running="$(docker compose ps --status running --services | sort | tr '\n' ',')"
    if [[ "${tls_code}" != "000" && "${running}" == *"osctrl-tls,"* ]]; then
        echo "osctrl is up (nginx=${tls_code}, running=${running})"
        break
    fi
    if (( $(date +%s) > deadline )); then
        echo "Timed out waiting for osctrl to become ready" >&2
        docker compose ps >&2 || true
        docker compose logs --tail 50 >&2 || true
        exit 1
    fi
    sleep 5
done
