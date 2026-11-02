# Roadmap

Each item should become a GitHub issue (label `roadmap`).

## Planned
- [ ] Prometheus and Grafana with AMD's metrics exporter: configs in `monitoring/`, not yet tested on the MI210
- [ ] KubeVirt VM with the MI210 passed through
- [ ] SR-IOV with AMD's GIM driver. It's validated on RHEL 9.4 hosts, and a consumer board may not cooperate.
- [ ] vLLM serving on the MI210
- [ ] Package `passthrough-check` as .deb and .rpm

## Tool ideas
- [ ] `--watch` mode to catch link speed under load
- [ ] Flag `pcihole64` / BAR size problems (read `resource` and compare against guest-visible space)
