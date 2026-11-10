#!/usr/bin/env bash
#
# Kubernetes worker-node join helper
#
# Run this script on the worker node.
# Generate a fresh command on the control plane with:
#   sudo kubeadm token create --print-join-command
#
# Never commit a real kubeadm token, CA hash, or private IP address.

set -euo pipefail

CONTROL_PLANE_ENDPOINT="${CONTROL_PLANE_ENDPOINT:-}"
JOIN_TOKEN="${JOIN_TOKEN:-}"
CA_CERT_HASH="${CA_CERT_HASH:-}"

if [[ -z "$CONTROL_PLANE_ENDPOINT" || -z "$JOIN_TOKEN" || -z "$CA_CERT_HASH" ]]; then
  cat >&2 <<'EOF'
Missing required environment variables.

Set these values from the fresh kubeadm join command:
  CONTROL_PLANE_ENDPOINT  Example: 10.0.1.10:6443
  JOIN_TOKEN              Bootstrap token from kubeadm
  CA_CERT_HASH            SHA256 CA hash, without the "sha256:" prefix

Then run this script with sudo.
EOF
  exit 1
fi

if [[ ! "$CA_CERT_HASH" =~ ^[[:xdigit:]]{64}$ ]]; then
  echo "CA_CERT_HASH must be a 64-character SHA256 hex string." >&2
  exit 1
fi

echo "Joining Kubernetes cluster at $CONTROL_PLANE_ENDPOINT ..."
kubeadm join "$CONTROL_PLANE_ENDPOINT" \
  --token "$JOIN_TOKEN" \
  --discovery-token-ca-cert-hash "sha256:$CA_CERT_HASH"
