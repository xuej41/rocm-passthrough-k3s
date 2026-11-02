# Later

- KubeVirt VM with the MI210
- SR-IOV with AMD's GIM driver. It's only validated on RHEL 9.4 hosts, so a consumer board might not cooperate
- vLLM on the MI210
- .deb / .rpm for passthrough-check

passthrough-check:

- check the slot link too, not just the GPU's. The MI210 has its own PCIe switch, so the GPU always reports x16 even though the slot is x8
- `--watch` to catch the link dropping under load
- flag BAR / pcihole64 problems
