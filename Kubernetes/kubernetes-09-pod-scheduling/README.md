# Kubernetes 09: Pod Scheduling — Node Selection, Affinity, Taints & Tolerations

This hands-on lab explores how Kubernetes assigns Pods to Nodes and how to influence placement with node selection, affinity, and taints/tolerations.

## Learning objectives

- Understand the role of `kube-scheduler` and feasible Nodes.
- Pin Pods to a Node with `nodeName`.
- Select Nodes by labels with `nodeSelector`.
- Use required and preferred node affinity.
- Co-locate workloads with Pod affinity.
- Control Node admission with taints and tolerations.

## Lab outline

1. [Prepare the cluster](#1-prepare-the-cluster)
2. [Scheduling concepts](#2-scheduling-concepts)
3. [nodeName](#3-nodename)
4. [nodeSelector](#4-nodeselector)
5. [Node affinity](#5-node-affinity)
6. [Pod affinity](#6-pod-affinity)
7. [Taints and tolerations](#7-taints-and-tolerations)
8. [Cleanup](#8-cleanup)

## Prerequisites

- A Kubernetes cluster with one control-plane Node and at least one worker.
- `kubectl` access with permission to label and taint Nodes.
- Examples use Node names `kube-master` and `kube-worker`; replace them with the names in your cluster.
- The original lab specifies Ubuntu 20.04. [Killercoda playgrounds](https://killercoda.com/playgrounds) can be used for practice.

## 1. Prepare the cluster

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Confirm that the Nodes are `Ready`.

## 2. Scheduling concepts

The `kube-scheduler` watches for Pods without an assigned Node. It filters Nodes against the Pod's requirements and scores feasible candidates. If no Node satisfies a hard constraint, the Pod remains `Pending`.

| Mechanism | What it does |
| --- | --- |
| `nodeName` | Directly names a Node and bypasses scheduler selection |
| `nodeSelector` | Requires matching Node labels |
| Node affinity | Adds expressive required or preferred Node-label rules |
| Pod affinity | Places Pods in a topology with matching Pods |
| Taints and tolerations | Repels Pods unless they tolerate a Node's taint |

## 3. nodeName

Start with an ordinary NGINX Deployment:

```bash
kubectl apply -f manifests/nginx-deployment.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-deployment.yaml
```

A typical kubeadm control-plane Node has a `NoSchedule` taint. Inspect it before temporarily removing it for the demonstration:

```bash
kubectl describe node kube-master | grep -i taint
kubectl taint nodes kube-master node-role.kubernetes.io/control-plane:NoSchedule-
```

The command applies to clusters using the standard control-plane taint. Older clusters may use `node-role.kubernetes.io/master:NoSchedule`; use the exact key shown by `kubectl describe node`.

Now deploy the baseline workload again and observe that the control-plane can receive workloads too:

```bash
kubectl apply -f manifests/nginx-deployment.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-deployment.yaml
```

The `nodeName` field goes inside the Pod template's `spec`:

```yaml
spec:
  template:
    spec:
      nodeName: kube-master
      containers:
        - name: nginx
          image: nginx
          ports:
            - containerPort: 80
```

Try the complete example:

```bash
kubectl apply -f manifests/nginx-node-name.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-node-name.yaml
```

**Trade-off:** `nodeName` bypasses the scheduler. If the named Node is missing or cannot run the Pod, Kubernetes will not select a different Node. Node names may also be unstable in cloud environments. Prefer label-based constraints for general workloads.

## 4. nodeSelector

`nodeSelector` is the simplest recommended label-based constraint. Every key-value pair must match a label on the selected Node.

Label the control-plane Node:

```bash
kubectl label nodes kube-master size=large
kubectl get nodes --show-labels
```

The example manifest contains:

```yaml
spec:
  template:
    spec:
      nodeSelector:
        size: large
```

Apply, inspect, and remove the workload:

```bash
kubectl apply -f manifests/nginx-node-selector.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-node-selector.yaml
kubectl label node kube-master size-
```

## 5. Node affinity

Node affinity is more expressive than `nodeSelector`. It supports hard requirements and soft preferences.

| Rule | Meaning |
| --- | --- |
| `requiredDuringSchedulingIgnoredDuringExecution` | Must match when scheduling; otherwise the Pod stays Pending |
| `preferredDuringSchedulingIgnoredDuringExecution` | Preference used in scoring; another eligible Node may be selected |

The `IgnoredDuringExecution` suffix means that changing a Node's labels later does not, by itself, evict a Pod that is already running there.

### Required affinity

Label a Node and check the label:

```bash
kubectl label nodes kube-master size=large
kubectl get nodes --show-labels
```

This rule accepts Nodes labelled `size=large` or `size=medium`:

```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: size
              operator: In
              values:
                - large
                - medium
```

Apply the required-affinity example:

```bash
kubectl apply -f manifests/nginx-node-affinity-required.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-node-affinity-required.yaml
```

Remove the label and try again. If no Node matches, the new Pods remain Pending:

```bash
kubectl label node kube-master size-
kubectl apply -f manifests/nginx-node-affinity-required.yaml
kubectl get pods -o wide
kubectl describe pod <pending-pod-name>
kubectl delete -f manifests/nginx-node-affinity-required.yaml
```

### Preferred affinity

A preferred rule influences scheduling scores but does not make the matching label mandatory:

```yaml
affinity:
  nodeAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
      - weight: 10
        preference:
          matchExpressions:
            - key: size
              operator: In
              values:
                - large
                - medium
```

Each weight is from 1 to 100. The scheduler combines the preference with other scoring factors.

```bash
kubectl apply -f manifests/nginx-node-affinity-preferred.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-node-affinity-preferred.yaml
```

## 6. Pod affinity

Pod affinity selects placement based on labels of other Pods. Here, the application Pods require a Node topology that already contains a database Pod labelled `tier=db`.

Create the database Pod first:

```bash
kubectl apply -f manifests/database-pod.yaml
kubectl get pods -o wide --show-labels
```

The application manifest uses this rule:

```yaml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchExpressions:
            - key: tier
              operator: In
              values:
                - db
        topologyKey: kubernetes.io/hostname
```

With `kubernetes.io/hostname` as the topology key, the matching Pods must be on the same Node:

```bash
kubectl apply -f manifests/shop-pod-affinity.yaml
kubectl get pods -o wide
kubectl delete -f manifests/shop-pod-affinity.yaml
kubectl delete -f manifests/database-pod.yaml
```

If no matching database Pod exists, the required-affinity Pods can remain Pending. Create the database Pod before the application.

## 7. Taints and tolerations

A taint repels Pods from a Node. A toleration allows a Pod to be considered for that Node, but does not force the scheduler to place it there.

Inspect current taints and add a `NoSchedule` taint to the worker:

```bash
kubectl describe node kube-worker | grep -i taint
kubectl taint nodes kube-worker color=blue:NoSchedule
kubectl describe node kube-worker | grep -i taint
```

Deploy a workload without a matching toleration. It should avoid the tainted worker when another eligible Node exists:

```bash
kubectl apply -f manifests/nginx-deployment.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-deployment.yaml
```

A toleration can match the exact key and value with `Equal`:

```yaml
tolerations:
  - key: color
    operator: Equal
    value: blue
    effect: NoSchedule
```

Or tolerate any value for that key with `Exists`:

```yaml
tolerations:
  - key: color
    operator: Exists
    effect: NoSchedule
```

The included example uses `Exists`:

```bash
kubectl apply -f manifests/nginx-toleration.yaml
kubectl get pods -o wide
kubectl delete -f manifests/nginx-toleration.yaml
```

**Remember:** Taints/tolerations control which Pods are allowed onto a Node; they do not select a destination. Use `nodeSelector` or node affinity to constrain placement.

## 8. Cleanup

Remove the worker taint and any temporary label. If you removed the control-plane taint, restore it after deleting the test workloads:

```bash
kubectl taint nodes kube-worker color=blue:NoSchedule-
kubectl label node kube-master size-
kubectl taint nodes kube-master node-role.kubernetes.io/control-plane:NoSchedule
```

If your cluster uses the legacy `node-role.kubernetes.io/master:NoSchedule` taint, restore that key instead. Verify the cluster:

```bash
kubectl get nodes
kubectl describe node kube-master | grep -i taint
kubectl describe node kube-worker | grep -i taint
kubectl get pods -A
```

## Files

```text
kubernetes-09-pod-scheduling/
├── README.md
└── manifests/
    ├── database-pod.yaml
    ├── nginx-deployment.yaml
    ├── nginx-node-affinity-preferred.yaml
    ├── nginx-node-affinity-required.yaml
    ├── nginx-node-name.yaml
    ├── nginx-node-selector.yaml
    ├── nginx-toleration.yaml
    └── shop-pod-affinity.yaml
```

## References

- [Assigning Pods to Nodes](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/)
- [Pod Affinity and Anti-Affinity](https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/#affinity-and-anti-affinity)
- [Taints and Tolerations](https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/)

---

*Educational lab: verify Node names, labels, and taints in your own cluster before running the commands.*
