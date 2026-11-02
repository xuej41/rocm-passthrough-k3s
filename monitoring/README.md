# GPU monitoring: Prometheus + Grafana

Live MI210 metrics (activity, power, temperature, VRAM, clocks, PCIe link, and which pod holds the GPU) on a Grafana dashboard.

```
MI210 ──► AMD Device Metrics Exporter ──(HTTP :5000/metrics)──► Prometheus ──(PromQL)──► Grafana
          reads the GPU via amdsmi          scrapes every 5s,       stores time series      dashboards/mi210.json
```

- **Exporter**: AMD's [Device Metrics Exporter](https://github.com/ROCm/device-metrics-exporter). It serves the GPU's current readings as text and keeps no history.
- **Prometheus**: pulls `/metrics` on a schedule and stores every value with a timestamp.
- **Grafana**: draws panels from PromQL queries against Prometheus.

**Run it where the GPU is visible.** Before passthrough that's the host. While the MI210 is passed through, the host can't see it, so run the stack **inside the guest**. A full PCIe passthrough guest sees the whole card, so you get the same metrics as on bare metal. Some metrics are unavailable only for SR-IOV virtual functions, which this setup doesn't use.

## Option A: Kubernetes (k3s)

Needs `helm` and a working `kubectl`. For k3s, copy the kubeconfig first:

```bash
mkdir -p ~/.kube && sudo cp /etc/rancher/k3s/k3s.yaml ~/.kube/config && sudo chown $USER ~/.kube/config
monitoring/k8s/install.sh
```

The script installs:

| What | Chart | Namespace |
|---|---|---|
| Prometheus, Grafana, Prometheus Operator | `prometheus-community/kube-prometheus-stack` 92.16.2 | `monitoring` |
| AMD exporter (DaemonSet + ServiceMonitor) | `amd-exporter/device-metrics-exporter-charts` v1.5.3 | `kube-amd-gpu` |
| MI210 dashboard (ConfigMap the Grafana sidecar loads) | — | `monitoring` |

When it finishes it prints the URLs and a random Grafana password. Grafana is at `http://<node-ip>:30300` and Prometheus at `:30090`. Prometheus keeps 15 days of data on a 10 Gi volume from k3s's `local-path` provisioner.

The exporter reads the kubelet's pod-resources API, so when a pod holds `amd.com/gpu`, its metrics carry `pod` and `namespace` labels. The dashboard's **Pods using this GPU** table uses that.

Remove everything with `monitoring/k8s/uninstall.sh`.

## Option B: Docker Compose (no Kubernetes)

```bash
docker compose -f monitoring/docker/compose.yaml up -d
curl -s localhost:5000/metrics | grep -m5 '^gpu_'    # exporter is reading the GPU
```

Grafana is at `http://<machine>:3000` (first login `admin` / `admin`, then it asks for a new password). Prometheus and the exporter only listen on localhost; use `ssh -L 9090:localhost:9090 <machine>` to reach Prometheus remotely. Stop with `docker compose -f monitoring/docker/compose.yaml down`, adding `-v` to delete stored data.

## The dashboard

`dashboards/mi210.json` loads automatically in both options. Pick the host and GPU at the top.

| Panel | Metric(s) |
|---|---|
| Compute activity, Activity | `gpu_gfx_activity`, `gpu_umc_activity` |
| Power | `gpu_power_usage` (falls back to `gpu_average_package_power`) |
| Edge temperature, Temperature | `gpu_edge_temperature`, `gpu_memory_temperature` |
| VRAM used, VRAM | `gpu_used_vram`, `gpu_total_vram` (MB) |
| PCIe speed | `pcie_speed`, `pcie_max_speed` (GT/s) |
| Health | `gpu_health` |
| Clocks | `gpu_clock{clock_type="system"\|"memory"}` |
| Pods using this GPU | `gpu_gfx_activity{pod!=""}` |

Metric names come from the exporter's [metrics list](https://github.com/ROCm/device-metrics-exporter/blob/main/docs/configuration/metricslist.md). Many metrics there apply only to MI300-series cards (junction temperature, PCIe bandwidth and replay counters, XGMI), so the dashboard sticks to ones listed for MI2xx.

AMD also publishes larger, cluster-oriented dashboards in the exporter repo's [`grafana/`](https://github.com/ROCm/device-metrics-exporter/tree/main/grafana) folder. To try one, go to **Dashboards → New → Import**, upload the JSON, and pick the Prometheus data source.

## Using it with the benchmark

Open the dashboard, set the time range to *Last 15 minutes*, and run `bench/run.sh baremetal` (or `guest`). GEMM shows up as compute activity and power near their peaks, and the copy tests show memory controller activity. Screenshots of both runs make a good companion to `bench/results/comparison.md`.

## Troubleshooting

- **Panels say "No data"**: check that Prometheus is scraping the exporter. In Prometheus, open **Status → Targets**; the exporter should be `UP`. In k8s, run `kubectl -n kube-amd-gpu get pods,servicemonitor`.
- **The exporter shows a second GPU**: on the host, the RX 480 may be listed too. Pick the MI210's `gpu_id` at the top of the dashboard.
- **One panel is empty but others work**: that metric isn't reported for this card or driver. Check it with `curl <exporter>:5000/metrics | grep <name>`.
- **Before unloading amdgpu or starting the VM on the host**: stop the exporter first, because it holds the GPU open. Run `docker compose ... stop exporter`, or in k8s scale the DaemonSet away from the node.
