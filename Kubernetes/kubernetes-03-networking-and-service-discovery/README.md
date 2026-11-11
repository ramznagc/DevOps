# Kubernetes 03 — Networking and Service Discovery

<p>
  <img src="https://img.shields.io/badge/Kubernetes-Services-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes Services" />
  <img src="https://img.shields.io/badge/Topics-ClusterIP%20%7C%20NodePort%20%7C%20DNS-0A7B83" alt="Networking topics" />
</p>

A hands-on lesson covering Kubernetes networking fundamentals, Service resources, service discovery, DNS, endpoints, and access to applications running in Pods.

## Learning objectives

By completing this lesson, you will practise how to:

- Explain why Services are useful when Pods are created, deleted, or replaced.
- Group Pods with label selectors and expose them through a stable Service endpoint.
- Explore Kubernetes service discovery and DNS.
- Create and inspect `ClusterIP` and `NodePort` Services.
- Understand how Service endpoints change as a Deployment scales.
- Connect to a Service in another namespace.

## Lesson outline

1. [Set up the Kubernetes cluster](#1-set-up-the-kubernetes-cluster)
2. [Understand Kubernetes networking and Services](#2-understand-kubernetes-networking-and-services)
3. [Deploy the sample application](#3-deploy-the-sample-application)
4. [Create a ClusterIP Service](#4-create-a-clusterip-service)
5. [Expose the application with NodePort](#5-expose-the-application-with-nodeport)
6. [Inspect Service endpoints](#6-inspect-service-endpoints)
7. [Access a Service across namespaces](#7-access-a-service-across-namespaces)
8. [Clean up](#8-clean-up)

---

## 1. Set up the Kubernetes cluster

The source lesson uses an Ubuntu 22.04 cluster with two nodes: one control-plane node and one worker node. It references a CloudFormation template from the previous lesson.

> **Template note:** The referenced `cfn-template-to-create-k8s-cluster.yml` was not included with the uploaded lesson file. Use your own prepared cluster or a Kubernetes practice environment such as [Killercoda](https://killercoda.com/playgrounds).

Check the cluster:

```bash
kubectl cluster-info
kubectl get nodes
```

Make sure the nodes are ready before continuing.

## 2. Understand Kubernetes networking and Services

Kubernetes networking covers communication in several places:

- Containers in the same Pod can communicate through `localhost` and their container ports.
- Pods communicate with other Pods over the cluster network.
- A Service provides a stable way to reach a group of Pods.
- Services can be used for internal cluster communication or to expose an application outside the cluster.

### Why do we need a Service?

Pods are temporary. A Deployment may replace Pods during scaling, failures, or updates. Each Pod receives its own IP address, and that address can change when the Pod is replaced.

Connecting clients directly to a Pod IP is therefore unreliable. A Kubernetes Service provides a stable virtual IP and DNS name for the selected Pods, and can distribute traffic across them.

### Service discovery and DNS

Kubernetes provides service discovery through its cluster DNS system. A Service can be reached by its name from within the same namespace. A fully qualified DNS name follows this format:

```text
<service-name>.<namespace>.svc.cluster.local
```

For example:

```text
web-flask-svc.demo.svc.cluster.local
```

The Service uses a label selector to identify the Pods that should receive traffic.

## 3. Deploy the sample application

Create a working directory for the lesson:

```bash
mkdir service-lessons
cd service-lessons
```

Create `web-flask.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-flask-deploy
  labels:
    env: dev
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-flask
  template:
    metadata:
      labels:
        app: web-flask
    spec:
      containers:
        - name: web-flask-pod
          image: ondiacademy/cw_web_flask1
          ports:
            - containerPort: 5000
```

Apply the manifest and inspect the Pods:

```bash
kubectl apply -f web-flask.yaml
kubectl get pods -o wide
```

The Pod IP addresses shown by this command are internal cluster addresses. They may change when Pods are replaced.

### Create a test Pod

Create `forcurl.yaml`:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: forcurl
spec:
  containers:
    - name: forcurl
      image: ondiacademy/forping
      imagePullPolicy: IfNotPresent
  restartPolicy: Always
```

Apply it and open a shell:

```bash
kubectl apply -f forcurl.yaml
kubectl get pods
kubectl exec -it forcurl -- sh
```

From inside the test container, you can try reaching one of the current Pod IPs:

```sh
ping <POD_IP>
```

Replace `<POD_IP>` with an address shown by `kubectl get pods -o wide`. The source exercise uses ping to demonstrate Pod-to-Pod connectivity; whether ICMP responds can depend on the image and network configuration.

### Observe Pod replacement

Scale the Deployment down to zero:

```bash
kubectl scale deployment web-flask-deploy --replicas=0
kubectl get pods -o wide
```

Scale it back up:

```bash
kubectl scale deployment web-flask-deploy --replicas=3
kubectl get pods -o wide
```

Notice that the recreated Pods can have different IP addresses.

## 4. Create a ClusterIP Service

Explore the Service resource:

```bash
kubectl explain service
```

Create `web-svc.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-flask-svc
  labels:
    env: dev
spec:
  type: ClusterIP
  ports:
    - port: 3000
      targetPort: 5000
  selector:
    app: web-flask
```

Apply it and inspect the Service:

```bash
kubectl apply -f web-svc.yaml
kubectl get services -o wide
kubectl describe service web-flask-svc
```

In this manifest:

- `port: 3000` is the port exposed by the Service.
- `targetPort: 5000` is the port on the selected application containers.
- `selector: app: web-flask` selects Pods with the matching label.
- `ClusterIP` makes the Service reachable from inside the cluster.

From the test Pod, try the Service DNS name:

```bash
kubectl exec -it forcurl -- sh
```

Then, inside the container:

```sh
curl http://web-flask-svc:3000
```

The Service name resolves through cluster DNS. You can also use the Service ClusterIP, but the DNS name is more stable and readable.

## 5. Expose the application with NodePort

A `NodePort` Service exposes the application on a port on each node.

Update the `spec` section in `web-svc.yaml`:

```yaml
spec:
  type: NodePort
  ports:
    - port: 3000
      targetPort: 5000
  selector:
    app: web-flask
```

Apply the updated manifest and find the assigned NodePort:

```bash
kubectl apply -f web-svc.yaml
kubectl get service web-flask-svc
```

Kubernetes assigns a NodePort from its configured NodePort range (commonly `30000-32767`). The service can then be reached using:

```text
http://<NODE_PUBLIC_IP>:<NODE_PORT>
```

### Set a specific NodePort

The source exercise demonstrates using port `30036`. To request that port, use:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-flask-svc
  labels:
    env: dev
spec:
  type: NodePort
  ports:
    - nodePort: 30036
      port: 3000
      targetPort: 5000
  selector:
    app: web-flask
```

Apply and verify:

```bash
kubectl apply -f web-svc.yaml
kubectl get service web-flask-svc
```

> **AWS security note:** To test from outside the cluster, allow only the required NodePort in the relevant EC2 security group, and restrict the source to your trusted IP address. Do not expose the full NodePort range publicly.

## 6. Inspect Service endpoints

A Service's endpoints represent the Pods currently selected to receive traffic. As Pods are added, removed, or replaced, Kubernetes updates the endpoint information.

Inspect the Endpoint resource and list endpoints:

```bash
kubectl explain endpoints
kubectl get endpoints -o wide
```

Scale the Deployment to ten replicas:

```bash
kubectl scale deployment web-flask-deploy --replicas=10
kubectl get pods -o wide
kubectl get endpoints web-flask-svc -o wide
```

Compare the endpoint addresses with the Pod IP addresses. The Service tracks the Pods matching its selector.

## 7. Access a Service across namespaces

Services in the same namespace can be reached by their short name. To reach a Service in another namespace, include the namespace in the DNS name.

The source lesson uses the namespace `demo`.

### 7.1 Remove the default-namespace sample resources

From the dedicated `service-lessons` working directory containing only this lesson's manifests, run:

```bash
kubectl delete -f web-svc.yaml
kubectl delete -f web-flask.yaml
kubectl delete -f forcurl.yaml
```

### 7.2 Create the namespace

```bash
kubectl create namespace demo
```

### 7.3 Update the Deployment manifest

Add `namespace: demo` under `metadata` in `web-flask.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-flask-deploy
  namespace: demo
  labels:
    env: dev
spec:
  replicas: 3
  selector:
    matchLabels:
      app: web-flask
  template:
    metadata:
      labels:
        app: web-flask
    spec:
      containers:
        - name: web-flask-pod
          image: ondiacademy/cw_web_flask1
          ports:
            - containerPort: 5000
```

### 7.4 Update the Service manifest

Add `namespace: demo` under `metadata` in `web-svc.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web-flask-svc
  namespace: demo
  labels:
    env: dev
spec:
  type: NodePort
  ports:
    - port: 3000
      targetPort: 5000
      nodePort: 30036
  selector:
    app: web-flask
```

Apply the manifests and inspect resources:

```bash
kubectl apply -f web-flask.yaml
kubectl apply -f web-svc.yaml
kubectl get namespaces
kubectl get deployments,pods,services -n demo
kubectl get pods
kubectl get services
```

### 7.5 Test cross-namespace DNS

The test Pod created earlier in the `default` namespace can reach the Service in `demo` using its namespace-qualified name.

```bash
kubectl exec -it forcurl -- sh
```

Inside the container:

```sh
curl http://web-flask-svc.demo:3000
curl http://web-flask-svc.demo.svc.cluster.local:3000
```

Both names refer to the Service in the `demo` namespace.

## 8. Clean up

Remove the resources created for this exercise:

```bash
kubectl delete service web-flask-svc -n demo
kubectl delete deployment web-flask-deploy -n demo
kubectl delete namespace demo
kubectl delete pod forcurl
```

Verify that the sample resources have been removed:

```bash
kubectl get all -n demo
kubectl get pods
kubectl get services
```

## Quick command reference

| Task | Command |
|---|---|
| Show cluster information | `kubectl cluster-info` |
| List nodes | `kubectl get nodes` |
| List Pods with IPs | `kubectl get pods -o wide` |
| Explain Services | `kubectl explain service` |
| List Services | `kubectl get services` |
| Describe a Service | `kubectl describe service <SERVICE_NAME>` |
| List endpoints | `kubectl get endpoints` |
| Scale a Deployment | `kubectl scale deployment <NAME> --replicas=3` |
| List namespaces | `kubectl get namespaces` |

## References

- [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/)
- [Kubernetes DNS for Services and Pods](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Kubernetes networking model](https://kubernetes.io/docs/concepts/services-networking/)
- [Kubernetes EndpointSlices](https://kubernetes.io/docs/concepts/services-networking/endpoint-slices/)
- [Kubernetes kubectl reference](https://kubernetes.io/docs/reference/kubectl/)

---

<p align="center"><i>Hands-on Kubernetes learning lab — Kubernetes 03</i></p>
