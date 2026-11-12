# Kubernetes 05 — Secrets and Secret Types

<p>
  <img src="https://img.shields.io/badge/Kubernetes-Secrets-326CE5?logo=kubernetes&logoColor=white" alt="Kubernetes Secrets" />
  <img src="https://img.shields.io/badge/Lab-Secret%20Types-0A7B83" alt="Secret types lab" />
</p>

A hands-on lab demonstrating the built-in Kubernetes Secret types through a BookStore example. Each section follows the same flow: **need → solution → hands-on steps → what happens behind the scenes → decision**.

The central idea: `Opaque` does not validate a particular data format. Other built-in Secret types expect specific keys or formats and can reject incomplete data.

## Learning objectives

By completing this lesson, you will practise how to:

- Create and inspect Kubernetes Secrets.
- Explain why Base64 encoding is not encryption.
- Compare `Opaque`, `kubernetes.io/basic-auth`, `kubernetes.io/ssh-auth`, and `kubernetes.io/tls`.
- Use `kubernetes.io/dockerconfigjson` with `imagePullSecrets`.
- Recognize legacy ServiceAccount-token and Docker config Secret types.
- Inspect bootstrap-token Secrets created by kubeadm.
- Understand why RBAC and encryption at rest matter when handling Secrets.

## Secret types covered

| Secret type | Expected key / data | Typical consumer |
|---|---|---|
| `Opaque` | No type-specific key requirement | Application |
| `kubernetes.io/basic-auth` | `username`, `password` | Application / tool |
| `kubernetes.io/ssh-auth` | `ssh-privatekey` | Application / CI tool |
| `kubernetes.io/tls` | `tls.crt`, `tls.key` | Ingress / application |
| `kubernetes.io/dockerconfigjson` | `.dockerconfigjson` containing valid JSON | kubelet |
| `kubernetes.io/service-account-token` | ServiceAccount annotation; controller-populated data | Legacy integrations |
| `kubernetes.io/dockercfg` | `.dockercfg` containing valid JSON | Legacy registry integrations |
| `bootstrap.kubernetes.io/token` | kubeadm-managed token data | Node bootstrap |

> **Security note:** Secret data is commonly represented as Base64 in Kubernetes manifests and API responses. Base64 is encoding, not encryption. Anyone with permission to read a Secret can decode its values. Use least-privilege RBAC and configure encryption at rest for Secret data in etcd. Never commit real passwords, private keys, certificates, registry credentials, or live tokens.

## Repository files

| File | Purpose |
|---|---|
| `00-namespace.yaml` | Creates the isolated `secret-demo` namespace |
| `01-opaque.yaml` | Working Opaque Secret |
| `02-basic-auth.yaml` | Working Basic Auth Secret |
| `02-basic-auth-broken.yaml` | Deliberately invalid Basic Auth example |
| `03-ssh-auth-broken.yaml` | Deliberately invalid SSH Auth example |
| `04-tls-broken.yaml` | Deliberately invalid TLS example |
| `05-private-image-pod.yaml` | Pod referencing a registry pull Secret |
| `06-service-account-token.yaml` | Legacy ServiceAccount token example |
| `07-dockercfg-legacy.yaml` | Legacy Docker config Secret |

The files ending in `-broken.yaml` are intentionally invalid and are included to demonstrate validation errors. Do not apply all manifests with a wildcard.

## Prerequisites

- A Kubernetes cluster and a working `kubectl` context.
- OpenSSL and OpenSSH client tools for generating disposable demo material.
- Permission to create namespaces, Secrets, Pods, and ServiceAccounts.

The lesson can be practised locally with Docker Desktop Kubernetes or kind, or in a prepared kubeadm cluster.

## 1. Prepare the lab

Create the namespace:

```bash
kubectl apply -f 00-namespace.yaml
kubectl get namespace secret-demo
```

Generate a self-signed TLS certificate and a second, unrelated pair for the mismatch demonstration:

```bash
openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout tls.key -out tls.crt -subj "/CN=bookstore.local"

openssl req -x509 -nodes -newkey rsa:2048 -days 365 \
  -keyout other.key -out other.crt -subj "/CN=other"
```

Generate a disposable SSH key pair:

```bash
ssh-keygen -t ed25519 -N "" -f bookstore-git -C bookstore-ci -q
```

- `req -x509` creates a self-signed certificate for this demonstration.
- `-keyout` and `-out` choose the private-key and certificate filenames.
- `ssh-keygen` creates a private key and its corresponding public key.
- In a real environment, use a trusted certificate authority (for example, cert-manager with an approved issuer) and manage private keys securely.

<badge color="warning">Keep generated credentials out of Git</badge>

The generated files `tls.key`, `tls.crt`, `other.key`, `other.crt`, `bookstore-git`, and `bookstore-git.pub` must remain local. They are not part of this repository.

## 2. Opaque — `01-opaque.yaml`

**Need:** The BookStore API needs database credentials, but there is no special data format to validate.

**Solution:** Use the general-purpose `Opaque` Secret.

```bash
kubectl apply -f 01-opaque.yaml
kubectl get secret bookstore-db-secret -n secret-demo
kubectl get secret bookstore-db-secret -n secret-demo -o yaml
```

The manifest uses `stringData` for readable input. Kubernetes converts these values into the `data` representation when storing the Secret.

You can create the same general-purpose type with `kubectl create secret generic`.

**Decision:** Use Opaque when the application defines its own key names and no built-in Secret format is needed.

## 3. Basic Auth — `02-basic-auth.yaml`

**Need:** The BookStore admin panel needs a username and password.

**Solution:** Use `kubernetes.io/basic-auth` with the conventional `username` and `password` keys.

```bash
kubectl apply -f 02-basic-auth.yaml
kubectl get secret bookstore-admin -n secret-demo -o yaml
kubectl get secret bookstore-admin -n secret-demo \
  -o jsonpath='{.data.password}' | base64 -d
echo
```

The password in the sample file is a disposable demonstration value only. Replace it before using this pattern in any real environment.

### Deliberately broken example

```bash
kubectl apply -f 02-basic-auth-broken.yaml
```

This manifest uses `user` instead of the expected Basic Auth key names. Kubernetes rejects the incomplete typed Secret. If the same arbitrary key were stored as an Opaque Secret, this type-specific validation would not apply.

## 4. SSH Auth — `03-ssh-auth-broken.yaml`

**Need:** A CI process needs an SSH private key to access a private Git repository.

**Solution:** Create an SSH Auth Secret using the required `ssh-privatekey` data key:

```bash
kubectl create secret generic bookstore-git-ssh -n secret-demo \
  --type=kubernetes.io/ssh-auth \
  --from-file=ssh-privatekey=bookstore-git
```

Add the matching public key (`bookstore-git.pub`) to the Git service as a deploy key, where appropriate. Mount the Secret into the workload that needs it, and restrict access to that Secret with RBAC.

### Deliberately broken example

```bash
kubectl apply -f 03-ssh-auth-broken.yaml
```

The file uses `id_rsa` instead of `ssh-privatekey`, so the typed Secret fails validation. The placeholder is not a real private key.

**Security reminder:** Base64 does not protect private keys. Limit Secret read access and avoid exposing Secret values in logs or terminal recordings.

## 5. TLS — `04-tls-broken.yaml`

**Need:** The BookStore website will serve HTTPS using a certificate and its corresponding private key.

**Solution:** Create a TLS Secret from the generated pair:

```bash
kubectl create secret tls bookstore-tls -n secret-demo \
  --cert=tls.crt --key=tls.key
```

The TLS Secret format uses both `tls.crt` and `tls.key`.

To demonstrate a key/certificate mismatch, try the unrelated key:

```bash
kubectl create secret tls bookstore-tls-bad -n secret-demo \
  --cert=tls.crt --key=other.key
```

The kubectl command checks that the certificate and private key match before creating the Secret.

### Deliberately broken example

```bash
kubectl apply -f 04-tls-broken.yaml
```

The manifest omits `tls.key`, so the typed Secret is rejected.

## 6. Private registry credentials — `05-private-image-pod.yaml`

**Need:** The BookStore API image is hosted in a private container registry. The node needs registry credentials to pull it.

**Solution:** Create a `kubernetes.io/dockerconfigjson` Secret:

```bash
kubectl create secret docker-registry bookstore-regcred -n secret-demo \
  --docker-server=registry.bookstore.example \
  --docker-username=ci-bot \
  --docker-password='DEMO_ONLY_CHANGE_ME'
```

Inspect the Pod manifest:

```bash
kubectl apply -f 05-private-image-pod.yaml
kubectl get pod bookstore-api-private -n secret-demo
kubectl describe pod bookstore-api-private -n secret-demo
```

The Pod references the registry Secret through `imagePullSecrets`. The kubelet uses the registry credentials while pulling the image; the application container does not need to read the pull Secret itself.

> The registry domain and image in this exercise are fictional. The Pod is expected to reach `ErrImagePull` or `ImagePullBackOff` unless you replace them with a real registry and image that you can access.

## 7. ServiceAccount token — legacy Secret

The file `06-service-account-token.yaml` creates a ServiceAccount and a legacy `kubernetes.io/service-account-token` Secret annotated with the ServiceAccount name.

Apply and inspect metadata without printing the token value:

```bash
kubectl apply -f 06-service-account-token.yaml
kubectl describe secret bookstore-api-token -n secret-demo
```

The token controller can populate the Secret with token-related data. These legacy Secret-based tokens are long-lived and should generally be avoided for new integrations.

For a short-lived token, use TokenRequest through kubectl:

```bash
kubectl create token bookstore-api -n secret-demo --duration=10m
```

Treat the returned token as a credential. Do not paste it into source files, commit history, tickets, or chat.

## 8. Docker config — legacy Secret

The file `07-dockercfg-legacy.yaml` demonstrates the older `kubernetes.io/dockercfg` format.

```bash
kubectl apply -f 07-dockercfg-legacy.yaml
kubectl get secret bookstore-regcred-legacy -n secret-demo
```

This legacy format is included for comparison. For new registry-pull use cases, prefer `kubernetes.io/dockerconfigjson`.

## 9. Bootstrap token — inspect only

kubeadm manages bootstrap tokens for nodes joining a cluster. In a kubeadm-based cluster, inspect the token Secret metadata and token list without printing token values:

```bash
kubectl get secrets -n kube-system \
  --field-selector type=bootstrap.kubernetes.io/token
sudo kubeadm token list
```

To create a fresh join command when needed:

```bash
sudo kubeadm token create --print-join-command
```

A join command contains credential material. Share it only through a secure channel and never commit it to Git.

## 10. Compare the Secret types

| Type | Type-specific data / validation | Typical consumer |
|---|---|---|
| Opaque | No type-specific key validation | Application |
| basic-auth | Conventional username/password keys | Application / tool |
| ssh-auth | `ssh-privatekey` key | Application / CI tool |
| tls | `tls.crt` and `tls.key` keys | Ingress / application |
| dockerconfigjson | `.dockerconfigjson` with valid JSON | kubelet |
| dockercfg (legacy) | `.dockercfg` with valid JSON | kubelet |
| service-account-token (legacy) | ServiceAccount annotation; controller-populated data | Legacy integration |
| bootstrap token | kubeadm-managed token Secret | Joining node |

**Key takeaway:** Choose a typed Secret when a Kubernetes component expects a known format or key convention. Use Opaque for application-defined data. Secret type validation is not a substitute for access control or encryption.

## 11. Clean up

Delete the namespace to remove the lab resources:

```bash
kubectl delete namespace secret-demo
```

Remove the locally generated demo key and certificate files when you no longer need them:

```bash
rm -f tls.key tls.crt other.key other.crt bookstore-git bookstore-git.pub
```

## References

- [Kubernetes Secret types](https://kubernetes.io/docs/concepts/configuration/secret/#secret-types)
- [Kubernetes Secrets](https://kubernetes.io/docs/concepts/configuration/secret/)
- [Distribute credentials securely using Secrets](https://kubernetes.io/docs/tasks/inject-data-application/distribute-credentials-secure/)
- [ServiceAccount token administration](https://kubernetes.io/docs/reference/access-authn-authz/service-accounts-admin/)

---

<p align="center"><i>Hands-on Kubernetes learning lab — Kubernetes 05</i></p>
