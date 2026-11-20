# Kubernetes 10: Container Health Probes — Liveness, Readiness & Startup

Learn how Kubernetes checks container health and application availability using liveness, readiness, and startup probes. This lab demonstrates HTTP, TCP, and command-based checks, along with their effect on container restarts and Service traffic.

## Learning objectives

By the end of this lab, you will be able to:

- Explain the different purposes of liveness, readiness, and startup probes.
- Configure HTTP, TCP socket, and exec probes.
- Observe how failed liveness checks trigger container restarts.
- Prevent traffic from reaching Pods that are not ready.
- Protect slow-starting applications with a startup probe.
- Tune probe timing and thresholds for an application's behavior.

## Lab outline

1. [Prepare the cluster](#1-prepare-the-cluster)
2. [Liveness probes](#2-liveness-probes)
   - [HTTP GET](#http-get-probe)
   - [Command execution](#exec-probe)
   - [TCP socket](#tcp-socket-probe)
3. [Startup probes](#3-startup-probes)
4. [Readiness probes](#4-readiness-probes)
5. [Compare the three probe types](#5-compare-the-three-probe-types)
6. [Clean up](#6-clean-up)

## Prerequisites

- A Kubernetes cluster with one control-plane Node and at least one worker Node.
- `kubectl` configured to access the cluster.
- Permission to create Pods, Deployments, and Services.
- The examples use the educational images `clarusway/probes`, `clarusway/startupprobe`, and `clarusway/readinessprobe`. Ensure your environment can pull them.
- The original lab uses Ubuntu 20.04. You can also use an interactive environment such as [Killercoda](https://killercoda.com/playgrounds).

## 1. Prepare the cluster

Verify connectivity and Node readiness:

```bash
kubectl cluster-info
kubectl get nodes -o wide
```

Make sure the Nodes are `Ready` before creating the workloads.

## 2. Liveness probes

A liveness probe tells the kubelet whether a container is still functioning. If the configured liveness check fails enough consecutive times, kubelet restarts that container.

Liveness checks are useful for detecting situations such as a deadlock: the process still exists, but it can no longer make progress.

### HTTP GET probe

The HTTP example checks the `/healthz` endpoint on port `80`:

```yaml
livenessProbe:
  httpGet:
    path: /healthz
    port: 80
  initialDelaySeconds: 3
  periodSeconds: 3
```

Apply the example:

```bash
kubectl apply -f manifests/liveness-http.yaml
kubectl get pod liveness-http
kubectl describe pod liveness-http
```

The educational image initially responds successfully, then begins returning HTTP 500 after approximately 30 seconds. HTTP status codes from 200 through 399 are considered successful; other response codes are failures. Once the failure threshold is reached, kubelet restarts the container.

Watch the restart count:

```bash
kubectl get pod liveness-http -w
```

Inspect the Pod's events and previous container logs if needed:

```bash
kubectl describe pod liveness-http
kubectl logs liveness-http --previous
```

### Exec probe

An exec probe runs a command inside the container. A zero exit code means success; a non-zero exit code means failure.

The example creates `/tmp/healthy`, waits 30 seconds, removes the file, and then continues running:

```yaml
args:
  - /bin/sh
  - -c
  - touch /tmp/healthy; sleep 30; rm -f /tmp/healthy; sleep 600
livenessProbe:
  exec:
    command:
      - cat
      - /tmp/healthy
  initialDelaySeconds: 5
  periodSeconds: 5
```

Apply and inspect:

```bash
kubectl apply -f manifests/liveness-exec.yaml
kubectl describe pod liveness-exec
kubectl get pod liveness-exec -w
```

After the file is removed, `cat /tmp/healthy` exits unsuccessfully. When the liveness failure threshold is reached, Kubernetes restarts the container.

### TCP socket probe

A TCP probe attempts to open a connection to the specified port. If the connection succeeds, the probe succeeds; otherwise, it fails.

This example checks the MySQL port, `3306`:

```yaml
livenessProbe:
  tcpSocket:
    port: 3306
  initialDelaySeconds: 15
  periodSeconds: 20
```

Apply and inspect the Pod:

```bash
kubectl apply -f manifests/liveness-tcp.yaml
kubectl describe pod liveness-tcp
kubectl get pod liveness-tcp -w
```

The source exercise originally used port `8080`, which is not the standard MySQL listener port. This lab uses `3306`. The manifest includes a simple password only to make the demonstration image start; do not store real credentials directly in a manifest. Use a Kubernetes Secret for actual applications.

## 3. Startup probes

A startup probe determines when an application has finished starting. While a startup probe has not succeeded, Kubernetes does not run the container's liveness and readiness probes. This protects slow-starting applications from being restarted before initialization completes.

The example application returns HTTP 500 for roughly the first 60 seconds and then returns HTTP 200. Its startup probe is configured as follows:

```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 80
  failureThreshold: 5
  periodSeconds: 15
```

The configured startup window is approximately:

```text
failureThreshold × periodSeconds = 5 × 15 = 75 seconds
```

Apply the Pod:

```bash
kubectl apply -f manifests/startup-probe.yaml
kubectl get pod startup-probe -w
kubectl describe pod startup-probe
```

After the startup probe succeeds, the liveness probe becomes active. If the startup probe does not succeed within its allowed attempts, kubelet restarts the container according to the Pod's restart policy.

**Tip:** Set the startup probe's failure window to cover the application's realistic worst-case startup time, with an appropriate safety margin.

## 4. Readiness probes

A readiness probe tells Kubernetes whether a container is ready to receive traffic. When a Pod is not ready, it is excluded from the ready endpoints used by Services. The container is not restarted just because its readiness probe fails.

Readiness checks are useful when an application needs time to load configuration, warm caches, or establish dependencies after its process has started.

The example Deployment has three replicas and checks the `/healthz` endpoint:

```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 80
  initialDelaySeconds: 3
  periodSeconds: 3
  successThreshold: 10
  failureThreshold: 5
```

The educational image initially responds with HTTP 500 for approximately 45 seconds, then responds with HTTP 200. The example uses `successThreshold: 10` to demonstrate consecutive successes: after becoming healthy, it needs ten successful checks in a row before Kubernetes marks it ready. With a three-second period, this can add roughly 30 seconds after the endpoint starts succeeding. For most production workloads, the default success threshold of `1` is more common.

Apply the Deployment and Service:

```bash
kubectl apply -f manifests/readiness-deployment.yaml
kubectl get deployments
kubectl get pods -o wide
kubectl get services
kubectl get endpoints readiness-service
```

Observe endpoint membership while the readiness probe is failing and after it begins succeeding:

```bash
kubectl describe pod <pod-name>
kubectl get endpoints readiness-service -w
```

You can also inspect EndpointSlices, which are the modern API for Service backends:

```bash
kubectl get endpointslices -l kubernetes.io/service-name=readiness-service
```

A Pod that is running but not ready will not be included among the Service's ready backends. Once its readiness probe succeeds enough consecutive times, it becomes eligible to receive traffic.

Delete the example when finished:

```bash
kubectl delete -f manifests/readiness-deployment.yaml
```

## 5. Compare the three probe types

| Probe | Main question | On failure |
| --- | --- | --- |
| Startup | Has the application completed startup? | Container is restarted after the startup failure threshold is reached |
| Liveness | Is the running container still healthy? | Container is restarted after the liveness failure threshold is reached |
| Readiness | Can the container receive traffic now? | Pod is marked not ready and removed from ready Service endpoints; no restart is triggered by readiness alone |

You can configure all three probes on the same container:

- Use startup to protect applications with long initialization times.
- Use liveness to recover from unrecoverable application states.
- Use readiness to control when the application receives traffic.

A failed readiness probe does not prevent liveness checks from running. A configured startup probe, however, delays both readiness and liveness checks until startup succeeds.

## 6. Clean up

Delete all lab resources:

```bash
kubectl delete -f manifests/liveness-http.yaml --ignore-not-found
kubectl delete -f manifests/liveness-exec.yaml --ignore-not-found
kubectl delete -f manifests/liveness-tcp.yaml --ignore-not-found
kubectl delete -f manifests/startup-probe.yaml --ignore-not-found
kubectl delete -f manifests/readiness-deployment.yaml --ignore-not-found
```

Confirm that the lab Pods and Service have been removed:

```bash
kubectl get pods
kubectl get services
```

## Repository contents

```text
kubernetes-10-container-health-probes/
├── README.md
└── manifests/
    ├── liveness-exec.yaml
    ├── liveness-http.yaml
    ├── liveness-tcp.yaml
    ├── readiness-deployment.yaml
    └── startup-probe.yaml
```

## Reference

- [Kubernetes: Configure Liveness, Readiness and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/)

---

*This lab is intended for learning. Probe timings and thresholds should be tuned to the actual startup and health characteristics of each application.*
