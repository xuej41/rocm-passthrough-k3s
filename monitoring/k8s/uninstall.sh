#!/usr/bin/env bash
# removes what install.sh added, prometheus data included
set -euo pipefail

helm uninstall amd-exporter -n kube-amd-gpu || true
helm uninstall monitoring -n monitoring || true
kubectl delete namespace monitoring kube-amd-gpu --ignore-not-found

# helm leaves the prometheus operator CRDs behind:
#   kubectl get crd -o name | grep monitoring.coreos.com | xargs kubectl delete
