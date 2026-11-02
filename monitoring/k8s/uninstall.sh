#!/usr/bin/env bash
# Remove everything install.sh added. Prometheus data (PVC) is deleted too.
set -euo pipefail

helm uninstall amd-exporter -n kube-amd-gpu || true
helm uninstall monitoring -n monitoring || true
kubectl delete namespace monitoring kube-amd-gpu --ignore-not-found

# The Prometheus Operator CRDs stay installed (Helm never deletes CRDs). To remove them:
#   kubectl get crd -o name | grep monitoring.coreos.com | xargs kubectl delete
