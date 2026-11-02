#!/usr/bin/env bash
# Install Prometheus + Grafana (kube-prometheus-stack) and AMD's Device Metrics
# Exporter into the current Kubernetes cluster, plus the MI210 dashboard.
# Safe to re-run: every step is an install-or-upgrade.
set -euo pipefail

HERE="$(cd "$(dirname "$0")" && pwd)"
KPS_VERSION="${KPS_VERSION:-92.16.2}"
EXPORTER_VERSION="${EXPORTER_VERSION:-v1.5.3}"

command -v helm >/dev/null || {
  echo "helm not found. Install it: https://helm.sh/docs/intro/install/" >&2
  exit 1
}
kubectl get nodes >/dev/null || {
  echo "kubectl can't reach the cluster. For k3s:" >&2
  echo "  mkdir -p ~/.kube && sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config && sudo chown \$USER ~/.kube/config" >&2
  exit 1
}

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo add amd-exporter https://rocm.github.io/device-metrics-exporter >/dev/null
helm repo update prometheus-community amd-exporter

# Grafana admin password: random, stored in a Secret, kept across re-runs.
kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -
if ! kubectl -n monitoring get secret grafana-admin >/dev/null 2>&1; then
  kubectl -n monitoring create secret generic grafana-admin \
    --from-literal=admin-user=admin \
    --from-literal=admin-password="$(head -c 18 /dev/urandom | base64)"
fi

echo "== Prometheus + Grafana"
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version "$KPS_VERSION" -n monitoring \
  -f "$HERE/kube-prometheus-stack.values.yaml" --wait --timeout 10m

echo "== MI210 dashboard"
kubectl -n monitoring create configmap mi210-dashboard \
  --from-file=mi210.json="$HERE/../dashboards/mi210.json" \
  --dry-run=client -o yaml | kubectl apply -f -
kubectl -n monitoring label configmap mi210-dashboard grafana_dashboard=1 --overwrite

# After the stack, so the ServiceMonitor CRD already exists.
echo "== AMD Device Metrics Exporter"
helm upgrade --install amd-exporter amd-exporter/device-metrics-exporter-charts \
  --version "$EXPORTER_VERSION" -n kube-amd-gpu --create-namespace \
  -f "$HERE/amd-exporter.values.yaml" --wait --timeout 5m

NODE_IP="$(kubectl get nodes -o jsonpath='{.items[0].status.addresses[?(@.type=="InternalIP")].address}')"
PASS="$(kubectl -n monitoring get secret grafana-admin -o jsonpath='{.data.admin-password}' | base64 -d)"
cat <<MSG

Grafana:    http://$NODE_IP:30300   (admin / $PASS)  -> Dashboards > MI210 GPU
Prometheus: http://$NODE_IP:30090   (Status > Targets should show amd-exporter as UP)
MSG
