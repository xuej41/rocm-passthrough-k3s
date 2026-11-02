# Monitoring

AMD's Device Metrics Exporter → Prometheus → Grafana, with a dashboard for the MI210 (`dashboards/mi210.json`). Not tried on the card yet.

It has to run wherever the GPU is visible: on the host before passthrough, in the guest while the VM has the card. Stop it before starting the VM, because the exporter keeps the GPU open.

## k3s

Needs helm and a working kubectl.

```bash
monitoring/k8s/install.sh     # kube-prometheus-stack 92.16.2 + exporter chart v1.5.3
monitoring/k8s/uninstall.sh
```

Grafana is on :30300 (the password is printed at the end) and Prometheus on :30090. When a pod holds `amd.com/gpu`, the exporter tags its metrics with the pod name, and the "Pods using this GPU" table reads that.

## docker compose

```bash
docker compose -f monitoring/docker/compose.yaml up -d
curl -s localhost:5000/metrics | grep -m5 '^gpu_'
```

Grafana is on :3000 (admin/admin the first time). Prometheus and the exporter only listen on localhost.

## Dashboard

Shows activity, power, temps, VRAM, clocks, PCIe speed and health. I only used metrics the exporter's [metrics list](https://github.com/ROCm/device-metrics-exporter/blob/main/docs/configuration/metricslist.md) gives for MI2xx, since a lot of the others are MI300 only. If a panel is empty, check whether the card reports that metric with `curl localhost:5000/metrics | grep <name>`.
