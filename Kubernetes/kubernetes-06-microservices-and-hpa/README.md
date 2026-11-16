# Kubernetes 06 — Microservices and Horizontal Pod Autoscaling (HPA)

This lesson deploys a small Node.js + MongoDB ToDo application as two Kubernetes microservices, then demonstrates CPU-based Horizontal Pod Autoscaling with a separate `php-apache` workload.

## Learning objectives

- Deploy an application split into web and database workloads
- Connect workloads through Kubernetes Services and cluster DNS
- Provision persistent storage with a PersistentVolumeClaim
- Expose selected services with NodePort for a lab environment
- Explain CPU requests and limits and why HPA needs resource requests
- Install and verify Metrics Server
- Create, observe, and test an `autoscaling/v2` HorizontalPodAutoscaler

## Repository layout

```text
kubernetes-06-microservices-and-hpa/
├── README.md
├── todo-app/
│   ├── app/                  # Node.js application source
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env.example
│   ├── compose/
│   │   └── docker-compose.yaml
│   └── kubernetes/
│       ├── db-pvc.yaml
│       ├── db-deployment.yaml
│       ├── db-service.yaml
│       ├── web-deployment.yaml
│       ├── web-service.yaml
│       └── mongo-express.yaml
└── hpa/
    ├── php-apache.yaml
    ├── php-apache-hpa.yaml
    └── web-hpa.yaml
```

## Prerequisites

- A working Kubernetes cluster and a configured `kubectl`
- A default StorageClass for dynamic PVC provisioning, or adapt the PVC to your cluster
- Metrics Server installed and reporting node/pod metrics
- Docker with the Compose plugin for the local container exercise
- Permission to pull the images used in the lab

> **Storage note:** The ToDo database PVC requests 1Gi and relies on the cluster's default StorageClass. The original static `hostPath` example is intentionally not used: it is node-local and unsuitable as a portable multi-node storage design. For a static PV lab, create a PV that matches your cluster's storage environment.

## Part 1 — Run the application with Docker Compose

From the `todo-app` directory:

```bash
cp .env.example .env
docker compose -f compose/docker-compose.yaml up --build -d
docker compose -f compose/docker-compose.yaml ps
docker compose -f compose/docker-compose.yaml logs -f web
```

Open [http://localhost:3000](http://localhost:3000). Stop the stack with:

```bash
docker compose -f compose/docker-compose.yaml down
```

The named MongoDB volume is retained. To remove it as well, use `docker compose -f compose/docker-compose.yaml down -v`.

## Part 2 — Deploy the ToDo microservices to Kubernetes

Build and publish the web image to a registry accessible by your cluster. Replace the sample image in `todo-app/kubernetes/web-deployment.yaml` with your own image reference.

```bash
docker build -t YOUR_REGISTRY/todo-app:1.0 ./todo-app
docker push YOUR_REGISTRY/todo-app:1.0
```

Apply the manifests:

```bash
kubectl apply -f todo-app/kubernetes/
kubectl get pvc,pods,services
kubectl rollout status deployment/db-deployment
kubectl rollout status deployment/web-deployment
```

The web Pod connects to MongoDB using the internal DNS name `db-service`. Kubernetes DNS resolves that Service name to its ClusterIP; the database does not need a public IP.

For a quick lab access path:

```bash
kubectl get nodes -o wide
kubectl get svc web-service
```

Open the assigned NodePort on a worker node address. If running on AWS, restrict the instance security-group rule to your own trusted source IP. Do not expose MongoDB publicly.

### Optional: Mongo Express

The `mongo-express.yaml` manifest is an optional database administration UI. It is exposed as NodePort for demonstration only. Do not expose it to the public internet. For real environments, use authentication, network restrictions, and preferably port-forwarding:

```bash
kubectl port-forward service/mongo-express-service 8081:8081
```

## Part 3 — Deploy the HPA demonstration workload

The `php-apache` example is independent of the ToDo application. Apply its Deployment and Service:

```bash
kubectl apply -f hpa/php-apache.yaml
kubectl get deployment,service,pods
```

The Deployment defines CPU requests and limits. CPU utilization for an HPA is calculated relative to the requested CPU, so requests must be set for the relevant containers.

## Part 4 — Install and verify Metrics Server

HPA uses the Kubernetes resource metrics API for CPU/memory resource metrics. Metrics Server is a common implementation of that API.

Install a release appropriate for your cluster version by following the official project instructions:
- https://github.com/kubernetes-sigs/metrics-server
- https://github.com/kubernetes-sigs/metrics-server/releases

Then verify:

```bash
kubectl -n kube-system get deployment metrics-server
kubectl top nodes
kubectl top pods
```

If `kubectl top` fails or HPA reports `<unknown>`, inspect:

```bash
kubectl describe deployment metrics-server -n kube-system
kubectl get apiservice v1beta1.metrics.k8s.io
kubectl describe hpa
```

Do not blindly add `--kubelet-insecure-tls` in production. It disables certificate verification for kubelet connections and weakens transport security. Prefer correctly configured kubelet certificates and trusted CA settings. Some disposable lab environments may require a documented workaround.

## Part 5 — Create and observe Horizontal Pod Autoscalers

Apply the HPA resources:

```bash
kubectl apply -f hpa/php-apache-hpa.yaml
kubectl apply -f hpa/web-hpa.yaml
kubectl get hpa
kubectl describe hpa php-apache
```

The PHP/Apache workload scales between 2 and 10 replicas at a target average CPU utilization of 50%. The web workload scales between 1 and 5 replicas at the same target. The web HPA is optional; keep the database at a single replica because this sample MongoDB deployment is not configured as a replica set.

Watch the resources:

```bash
kubectl get hpa,pods -w
```

Generate load against the PHP/Apache Service from inside the cluster:

```bash
kubectl run load-generator --rm -it --restart=Never --image=busybox:1.36 -- /bin/sh
```

At the BusyBox prompt:

```sh
while true; do wget -q -O- http://php-apache-service >/dev/null; done
```

In another terminal, observe:

```bash
kubectl get hpa
kubectl get deployment php-apache
kubectl top pods
```

Stop the loop with Ctrl+C. HPA scale-down is intentionally gradual and may take a few minutes.

## Troubleshooting checklist

| Symptom | What to check |
|---|---|
| PVC remains Pending | Default StorageClass, available capacity, provisioner events |
| Web Pod cannot connect to MongoDB | `DBHOST`, Service selector/endpoints, Pod logs |
| `kubectl top` fails | Metrics Server Pod, APIService, kubelet connectivity |
| HPA target is `<unknown>` | Metrics API health and CPU requests on every relevant container |
| HPA does not scale | Load level, HPA events, CPU requests, min/max replicas |
| NodePort is unreachable | Service endpoints, node firewall/security group, NodePort |

## Cleanup

```bash
kubectl delete -f hpa/
kubectl delete -f todo-app/kubernetes/
```

If the PVC is retained by the storage provider, inspect it before deleting any backing volume. Docker Compose resources can be removed with `docker compose -f todo-app/compose/docker-compose.yaml down`.

## Security and lab limitations

- NodePort and Mongo Express are for controlled training environments only.
- Do not commit real credentials, kubeconfig files, registry tokens, or cloud keys.
- The sample MongoDB setup is a single instance, not a highly available production database.
- The manifests are educational starting points; production deployments need authentication, TLS, network policies, backups, probes, disruption budgets, and an appropriate storage solution.
- No live Kubernetes cluster validation is claimed by this repository update. Validate manifests against your target cluster before applying them.

## References

- https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/
- https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale-walkthrough/
- https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/
- https://kubernetes.io/docs/concepts/storage/persistent-volumes/
- https://github.com/kubernetes-sigs/metrics-server
