# AMD vs NVIDIA, layer by layer

| Layer             | This lab (AMD)                                | NVIDIA                                                       |
|-------------------|-----------------------------------------------|--------------------------------------------------------------|
| Kernel driver     | `amdgpu`, in-tree                             | Open kernel modules, out of tree; Nova in-tree for the future |
| User-space driver | ROCm inside the container image               | `libcuda` injected from the host; must match the kernel module |
| Container access  | Pass `/dev/kfd` and `/dev/dri`                | Container Toolkit with CDI (default since 1.18)              |
| Kubernetes        | ROCm device plugin (`amd.com/gpu`), AMD GPU Operator | NVIDIA device plugin (`nvidia.com/gpu`), GPU Operator  |
| Monitoring        | `rocm-smi`, AMD metrics exporter              | `nvidia-smi`, DCGM exporter                                  |
| Passthrough       | `vfio-pci`                                    | `vfio-pci`, identical                                        |
| Sharing           | MxGPU SR-IOV (GIM); partitions on MI300       | vGPU on SR-IOV VFs; MIG                                      |
| Topology          | `rocm-smi --showtopo`; Infinity Fabric        | `nvidia-smi topo -m`; NVLink and NVSwitch                    |

**In short:** passthrough is identical on NVIDIA. The real differences are how the user-mode driver reaches containers, and vGPU on SR-IOV.
