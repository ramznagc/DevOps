# Ingress rewrite-target annotation lab

This focused exercise demonstrates how the NGINX `rewrite-target` annotation changes the request path sent to a backend Service.

> **Lifecycle warning:** This exercise uses the community ingress-nginx controller. The project was retired on March 24, 2026 and no longer receives security fixes or releases. Use it only in an isolated learning environment, not for a new production deployment. See the [Kubernetes retirement notice](https://kubernetes.io/blog/2025/11/11/ingress-nginx-retirement/).

## Application behavior

The ClarusShop example has two backends:

- **Storefront:** serves its page from `/`.
- **Account:** the first image serves its page from `/account`; the alternate image serves the page from `/`.

The Kubernetes resources are in the `k8s/` directory. The Ingress resource is `ing.yaml`.

## Prerequisites

- A Kubernetes cluster with a compatible Ingress controller already installed.
- An IngressClass named `nginx` for the lab controller.
- `kubectl` configured for the target cluster.

The controller is not installed by these application manifests.

## Part 1 — Route without rewrite-target

In this first stage, the account application serves the `/account` path itself. The annotation is intentionally absent.

The relevant Ingress definition is:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ingress-clarusshop
spec:
  ingressClassName: nginx
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: storefront-service
                port:
                  number: 80
          - path: /account
            pathType: Prefix
            backend:
              service:
                name: account-service
                port:
                  number: 80
```

Apply the Deployments and Services, then the Ingress:

```bash
kubectl apply -f k8s/
kubectl apply -f ing.yaml
kubectl get pods,services,ingress
```

Get the address of your Ingress controller and test the account route:

```bash
curl http://<INGRESS-ADDRESS>/account
```

The request reaches `account-service` with the `/account` path, which the first account image handles.

## Part 2 — Route with rewrite-target

Now change the account Deployment to use the alternate image that serves the page from `/`:

```yaml
image: clarusway/cs-account-without-path
```

Update the Deployment:

```bash
kubectl set image deployment/account-deployment \
  account=clarusway/cs-account-without-path
kubectl rollout status deployment/account-deployment
```

Test the same URL again:

```bash
curl http://<INGRESS-ADDRESS>/account
```

The request still matches the `/account` Ingress path and reaches the account Service, but the backend application now serves only `/`. Without a rewrite, the backend receives `/account` and can return HTTP 404.

Add the annotation to `metadata` in `ing.yaml`:

```yaml
metadata:
  name: ingress-clarusshop
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
```

Apply the updated Ingress and test again:

```bash
kubectl apply -f ing.yaml
curl http://<INGRESS-ADDRESS>/account
```

The controller rewrites the matching request path to `/` before proxying it to the account backend.

## Important notes

- `rewrite-target` is an ingress-nginx-specific annotation, not a standard Kubernetes Ingress field.
- In this simplified example, the target is the backend root path `/`.
- A single rewrite annotation applies to the Ingress paths governed by that Ingress. For complex applications, use separate Ingress resources or carefully designed path rules and capture groups.
- The sample controller is retired upstream. Do not deploy it for production workloads.
- Replace `<INGRESS-ADDRESS>` with the actual address shown by `kubectl get ingress` or the controller Service. The address depends on the cluster environment.

## Files

- `ing.yaml` — Ingress routes for storefront and account.
- `k8s/account-deploy.yaml` — account Deployment.
- `k8s/account-service.yaml` — account Service.
- `k8s/storefront-deploy.yaml` — storefront Deployment.
- `k8s/storefront-service.yaml` — storefront Service.
