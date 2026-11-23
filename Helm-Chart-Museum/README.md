# Helm Chart Repository with ChartMuseum

A hands-on guide to hosting and publishing Helm charts with ChartMuseum. The lab covers a local-filesystem-backed ChartMuseum server, adding it as a Helm repository, uploading chart packages, publishing new versions, and managing releases installed from the repository.

> **Repository model:** ChartMuseum implements the classic HTTP Helm chart-repository API. It is different from a static repository hosted on GitHub Pages and from an OCI registry. For new platform designs, also evaluate OCI-compatible registries and the current Helm documentation.

## Learning objectives

By completing this lab, you will be able to:

- Explain the structure of a classic Helm chart repository.
- Install and run ChartMuseum with local filesystem storage.
- Add a ChartMuseum endpoint to the local Helm client.
- Package and upload charts through the ChartMuseum API.
- Publish chart updates and search available versions.
- Use the ChartMuseum Helm push plugin.
- Install, upgrade, inspect, and roll back a release.

## Contents

1. [Prerequisites and cluster setup](#1-prerequisites-and-cluster-setup)
2. [Install Helm](#2-install-helm)
3. [Understand chart repositories](#3-understand-chart-repositories)
4. [Install and start ChartMuseum](#4-install-and-start-chartmuseum)
5. [Package and upload a chart](#5-package-and-upload-a-chart)
6. [Publish chart updates](#6-publish-chart-updates)
7. [Use the ChartMuseum push plugin](#7-use-the-chartmuseum-push-plugin)
8. [Install and manage a release](#8-install-and-manage-a-release)
9. [Cleanup and security considerations](#9-cleanup-and-security-considerations)

## 1. Prerequisites and cluster setup

You need:

- A Kubernetes cluster with a working `kubectl` context.
- Helm 3 or a compatible Helm client.
- A Linux host or VM on which you can run ChartMuseum.
- Network access from your Helm client to the ChartMuseum endpoint.
- A chart directory, such as the `clarus-chart` created in the [Helm fundamentals guide](../Helm/README.md).

The original exercise uses an Ubuntu 22.04 cluster with one control-plane node and one worker node, provisioned using the CloudFormation template from the Kubernetes basic-operations lesson. You can also practice Kubernetes commands in [Killercoda](https://killercoda.com/playgrounds).

Check the cluster:

```bash
kubectl cluster-info
kubectl get nodes
```

## 2. Install Helm

Install Helm using the official [installation instructions](https://helm.sh/docs/intro/install/):

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

For a controlled environment, review the installer and pin a tested Helm version.

## 3. Understand chart repositories

A classic Helm chart repository is an HTTP(S) server that provides:

- An `index.yaml` file containing metadata for available chart versions.
- Packaged chart archives, usually named `<chart-name>-<version>.tgz`.

The archive contains the chart, while `index.yaml` tells Helm which chart versions exist and where their archives can be downloaded.

A repository can be hosted on static web hosting or served by a chart-repository application such as ChartMuseum. ChartMuseum additionally provides an API for uploading and deleting chart packages.

## 4. Install and start ChartMuseum

ChartMuseum is an open-source chart repository server written in Go. It supports local filesystem storage and several object-storage backends.

Follow the project's [installation instructions](https://github.com/helm/chartmuseum) and choose a release appropriate for your environment. The upstream install script used in the original lab is:

```bash
curl -fsSL https://raw.githubusercontent.com/helm/chartmuseum/main/scripts/get-chartmuseum | bash
chartmuseum --version
```

Review scripts before executing them, and pin a release in repeatable environments.

Create a directory for chart storage and start the server:

```bash
mkdir -p ./chartstorage

chartmuseum \
  --debug \
  --port=8080 \
  --storage="local" \
  --storage-local-rootdir="./chartstorage"
```

This command runs ChartMuseum in the foreground. Keep the process running while completing the remaining steps. In a separate terminal, test the endpoint:

```bash
curl -fsS http://localhost:8080/health
```

If ChartMuseum runs on a remote VM, replace `localhost` with its reachable DNS name or IP address. Allow inbound TCP port 8080 only from trusted client networks. Do not expose an unauthenticated test server to the public internet.

Add the endpoint to Helm:

```bash
helm repo add mylocalrepo http://<chartmuseum-host>:8080
helm repo list
helm repo update
helm search repo mylocalrepo
```

At this point, the repository may be empty. That is expected until a chart is uploaded.

## 5. Package and upload a chart

Package the chart directory. The chart's `Chart.yaml` must contain a valid chart name and version:

```bash
helm package clarus-chart
```

For example, the output may be `clarus-chart-0.1.0.tgz`.

Upload the package to ChartMuseum using its chart upload API:

```bash
curl --fail-with-body \
  --data-binary "@clarus-chart-0.1.0.tgz" \
  http://<chartmuseum-host>:8080/api/charts
```

ChartMuseum stores the archive and updates the repository index it serves. Refresh the Helm client and search:

```bash
helm repo update
helm search repo mylocalrepo
helm search repo mylocalrepo --versions
```

The local `helm repo index` command is primarily used to generate metadata for static chart repositories. For this ChartMuseum workflow, upload the package through the API; ChartMuseum manages its served index.

## 6. Publish chart updates

To publish another version, update the `version` field in `clarus-chart/Chart.yaml`. For example, change it from `0.1.0` to `0.1.1`, then package and upload the new archive:

```bash
helm package clarus-chart

curl --fail-with-body \
  --data-binary "@clarus-chart-0.1.1.tgz" \
  http://<chartmuseum-host>:8080/api/charts
```

Refresh the local cache and list all versions:

```bash
helm repo update
helm search repo mylocalrepo --versions
```

Each published chart version should have a unique version. Use semantic versioning and avoid replacing an existing version with different chart contents.

## 7. Use the ChartMuseum push plugin

The ChartMuseum project provides a Helm plugin that adds the `helm cm-push` command.

Install it from the [helm-push repository](https://github.com/chartmuseum/helm-push):

```bash
helm plugin list
helm plugin install https://github.com/chartmuseum/helm-push.git
helm plugin list
```

Push a chart directory to the configured ChartMuseum repository:

```bash
helm cm-push clarus-chart mylocalrepo
```

You can explicitly set the chart version for a push:

```bash
helm cm-push clarus-chart mylocalrepo --version="1.2.3"
```

Use a new version for each changed package. Then refresh and search:

```bash
helm repo update
helm search repo mylocalrepo --versions
```

The plugin is an alternative to manually packaging a chart and uploading the resulting archive with `curl`. Use one publishing method at a time for a given package to avoid confusion about which version was uploaded.

## 8. Install and manage a release

Before installing, ensure the chart template renders valid Kubernetes resources. For example, a ConfigMap template can use the release name and chart values:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-config
data:
  myvalue: "clarus-chart configmap example"
  course: {{ .Values.course | quote }}
  topic: {{ .Values.lesson.topic | quote }}
  time: {{ now | date "2006-01-02" | quote }}
  count: "first"
```

Publish this chart as a new chart version, then install it from the repository:

```bash
helm repo update
helm search repo mylocalrepo --versions
helm install from-local-repo mylocalrepo/clarus-chart
```

Inspect the release and the Kubernetes resource:

```bash
helm list
helm status from-local-repo
kubectl get configmaps
kubectl describe configmap from-local-repo-config
```

### 8.1 Upgrade the release

Change the template value, for example change `count` from `first` to `second`. Increment the chart version, package/push the new version, and refresh the repository cache:

```bash
helm cm-push clarus-chart mylocalrepo --version="1.2.5"
helm repo update
helm search repo mylocalrepo --versions
```

Upgrade the installed release:

```bash
helm upgrade from-local-repo mylocalrepo/clarus-chart
helm history from-local-repo
kubectl describe configmap from-local-repo-config
```

### 8.2 Upgrade to a specific chart version

You can select a chart package version during an upgrade:

```bash
helm upgrade from-local-repo mylocalrepo/clarus-chart --version 1.2.4
```

The `--version` flag selects the chart version. Helm's release revision is a separate value.

### 8.3 Roll back a release

Inspect the release history and roll back to a previous revision:

```bash
helm history from-local-repo
helm rollback from-local-repo 1
helm history from-local-repo
kubectl describe configmap from-local-repo-config
```

Rollback changes the deployed release to a previous revision; it does not delete chart packages from the repository.

## 9. Cleanup and security considerations

Uninstall the release and remove the repository from the local Helm configuration:

```bash
helm uninstall from-local-repo
helm repo remove mylocalrepo
helm repo list
```

Stop the ChartMuseum process with `Ctrl+C` in the terminal where it is running. Remove the local storage directory only if you no longer need the uploaded chart packages:

```bash
rm -rf ./chartstorage
```

> **Warning:** The last command permanently deletes the local chart repository data. Confirm the directory before running it.

### Security and operational notes

- The example uses plain HTTP and no authentication to keep the lab simple. Do not use this configuration for an internet-facing or production repository.
- Use HTTPS, authentication, network restrictions, backups, and access controls for a shared service.
- Persist the storage directory outside an ephemeral container or VM if chart packages must survive restarts or replacement.
- Pin ChartMuseum, Helm, and plugin versions in repeatable environments.
- Treat chart packages as deployable software: review templates, image references, permissions, and values before installation.
- Consider an OCI-compatible registry for new workflows; the classic repository API shown here is retained for this hands-on exercise.

## Further reading

- [ChartMuseum project](https://github.com/helm/chartmuseum)
- [ChartMuseum documentation](https://chartmuseum.com/)
- [ChartMuseum Helm push plugin](https://github.com/chartmuseum/helm-push)
- [Helm chart repositories](https://helm.sh/docs/topics/chart_repository/)
- [Helm OCI registries](https://helm.sh/docs/topics/registries/)
- [Helm fundamentals lab](../Helm/README.md)

---

*This is an educational lab. The commands and configuration should be adapted and security-reviewed before use in shared or production environments.*
