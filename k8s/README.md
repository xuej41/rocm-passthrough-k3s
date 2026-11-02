# k3s

```bash
curl -sfL https://get.k3s.io | sh -
sudo k3s kubectl get nodes

# AMD device plugin
kubectl create -f https://raw.githubusercontent.com/ROCm/k8s-device-plugin/master/k8s-ds-amdgpu-dp.yaml
kubectl describe node | grep amd.com/gpu     # should be 1, 2 means it's counting the RX 480

# reuse the local image instead of pulling it again
docker save rocm/dev-ubuntu-22.04:latest | sudo k3s ctr images import -

kubectl apply -f k8s/amd/pod-1gpu.yaml
kubectl logs rocm-smi-1gpu

kubectl apply -f k8s/amd/pod-2gpu.yaml
kubectl describe pod rocm-smi-2gpu           # Pending, Insufficient amd.com/gpu
```

The k3s kubeconfig is root-only. Use `sudo k3s kubectl`, or copy `/etc/rancher/k3s/k3s.yaml` to `~/.kube/config`.

`nvidia/` is for trying the same thing with a 4060 Ti in place of the RX 480. That needs the driver, the NVIDIA container toolkit (restart k3s afterwards so it picks up the `nvidia` runtime class) and NVIDIA's device plugin.
