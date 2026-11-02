# Kubernetes

Flow:

```bash
# k3s
curl -sfL https://get.k3s.io | sh -
sudo k3s kubectl get nodes

# practise these
kubectl get pods -A
kubectl describe node
kubectl logs <pod>
kubectl exec -it <pod> -- sh

# AMD device plugin (ROCm/k8s-device-plugin)
kubectl create -f https://raw.githubusercontent.com/ROCm/k8s-device-plugin/master/k8s-ds-amdgpu-dp.yaml
kubectl describe node | grep amd.com/gpu     # expect 1, not 2

# import the ROCm image from Docker instead of pulling it again
docker save rocm/dev-ubuntu-22.04:latest | sudo k3s ctr images import -

kubectl apply -f k8s/amd/pod-1gpu.yaml
kubectl logs rocm-smi-1gpu                   # should show the MI210

kubectl apply -f k8s/amd/pod-2gpu.yaml
kubectl describe pod rocm-smi-2gpu           # Pending: Insufficient amd.com/gpu
```

GPU metrics and dashboards: see [`monitoring/`](../monitoring/README.md).

If the node shows `amd.com/gpu: 2`, the plugin is counting the RX 480 too.

## Optional: NVIDIA path

Swap the RX 480 for the 4060 Ti. Install the driver and the NVIDIA Container Toolkit, then restart k3s; it creates the `nvidia` RuntimeClass itself. Deploy NVIDIA's device plugin, then `kubectl apply -f k8s/nvidia/pod-nvidia-smi.yaml`.
