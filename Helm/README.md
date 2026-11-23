# Helm Fundamentals

A hands-on guide to Helm 3+ and the Kubernetes package lifecycle. This lesson covers Helm's core concepts, installing and managing releases, building a reusable chart, working with templates and values, and publishing charts through a static GitHub-hosted chart repository.

> **Scope:** The commands use Helm 3-compatible syntax. Check the current Helm documentation for installation instructions and version-specific behavior before using them in a production environment.

## Learning objectives

By completing this guide, you will be able to:

- Explain the relationship between charts, repositories, and releases.
- Search for charts in Artifact Hub and configured repositories.
- Install, inspect, upgrade, roll back, and uninstall releases.
- Create a chart and customize its templates with values.
- Use built-in template objects and functions.
- Add installation notes and manage chart versions.
- Publish packaged charts from a GitHub repository using the classic HTTP chart-repository format.

## Contents

1. [Prerequisites and cluster setup](#1-prerequisites-and-cluster-setup)
2. [Install Helm](#2-install-helm)
3. [Helm concepts](#3-helm-concepts)
4. [Find and install charts](#4-find-and-install-charts)
5. [Create a chart](#5-create-a-chart)
6. [Values and templates](#6-values-and-templates)
7. [Built-in objects and template functions](#7-built-in-objects-and-template-functions)
8. [Release notes, upgrades, and rollback](#8-release-notes-upgrades-and-rollback)
9. [Host a chart repository with GitHub Pages or static hosting](#9-host-a-chart-repository-with-github-pages-or-static-hosting)
10. [Cleanup](#10-cleanup)

## 1. Prerequisites and cluster setup

You need:

- A working Kubernetes cluster and a configured `kubectl` context.
- A Linux shell or another supported Helm installation environment.
- Git and a GitHub repository if you want to complete the publishing exercise.

The original lab uses an Ubuntu 22.04 cluster with one control-plane node and one worker node, provisioned using the CloudFormation template from the Kubernetes basic-operations lesson. A browser-based alternative for practicing Kubernetes is [Killercoda](https://killercoda.com/playgrounds).

Check cluster connectivity:

```bash
kubectl cluster-info
kubectl get nodes
```

Both nodes should be in the `Ready` state before continuing.

## 2. Install Helm

Install Helm by following the official [installation guide](https://helm.sh/docs/intro/install/). The upstream installation script can be used on Linux:

```bash
curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
helm version
```

Review the script before executing it in environments with strict security requirements. For repeatable environments, pin and verify the Helm version rather than always installing the latest release.

Useful references:

- [Helm documentation](https://helm.sh/docs/)
- [Helm installation](https://helm.sh/docs/intro/install/)
- [Helm releases](https://github.com/helm/helm/releases)

## 3. Helm concepts

Helm has three foundational concepts:

| Concept | Meaning |
|---|---|
| **Chart** | A package containing the files and templates needed to describe a Kubernetes application. |
| **Repository** | A location where packaged charts and repository metadata are published and shared. |
| **Release** | A named installation of a chart in a Kubernetes cluster. |

A chart can be installed more than once in the same cluster. Each installation creates a separate release with its own name and release history.

In short: **Helm installs charts into Kubernetes and manages each installation as a release.**

## 4. Find and install charts

Helm can search two types of sources:

- `helm search hub` searches Artifact Hub, which catalogs charts from many publishers.
- `helm search repo` searches repositories configured in your local Helm client.

Search Artifact Hub:

```bash
helm search hub
helm search hub wordpress
```

Add a chart repository and inspect it:

```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo list
helm repo update
helm search repo bitnami
```

Repository contents are cached locally. Run `helm repo update` to refresh that cache.

Inspect a chart before installing it:

```bash
helm show chart bitnami/mysql
helm show values bitnami/mysql
helm show all bitnami/mysql
```

Install a chart and inspect the release:

```bash
helm install mysql-release bitnami/mysql
helm list
helm status mysql-release
```

The chart's default values are used unless you provide overrides. For example, a WordPress chart can be customized with `--set`:

```bash
helm install my-release bitnami/wordpress \
  --set wordpressUsername=admin \
  --set wordpressPassword='change-me' \
  --set mariadb.auth.rootPassword='change-me-too'
```

> **Security:** These values are for demonstrating Helm syntax only. Do not use example passwords in real environments. Values passed through command-line arguments may be exposed in shell history or process information. Use an appropriate secret-management workflow for credentials.

Remove the example releases when finished:

```bash
helm uninstall my-release
helm uninstall mysql-release
```

## 5. Create a chart

Generate a starter chart:

```bash
helm create clarus-chart
tree clarus-chart
```

A generated chart contains a `Chart.yaml` metadata file, a `values.yaml` defaults file, templates, and supporting files. For this introductory exercise, remove the generated templates so that the chart can be built up one resource at a time:

```bash
rm -rf clarus-chart/templates/*
```

Create `clarus-chart/templates/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: clarus-chart-config
data:
  myvalue: "clarus-chart configmap example"
  course: "DevOps"
```

Render and install the chart:

```bash
helm template helm-demo clarus-chart
helm install helm-demo clarus-chart
helm list
kubectl get configmap clarus-chart-config
kubectl describe configmap clarus-chart-config
```

Uninstall it before the next variation:

```bash
helm uninstall helm-demo
```

## 6. Values and templates

Chart defaults are stored in `values.yaml`. Values are available to templates through the `.Values` object.

Set `clarus-chart/values.yaml` to:

```yaml
course: DevOps
```

Update `clarus-chart/templates/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: clarus-chart-config
data:
  myvalue: "clarus-chart configmap example"
  course: {{ .Values.course | quote }}
```

Render the chart without installing it:

```bash
helm install --debug --dry-run mydryrun clarus-chart
```

Install it and inspect the rendered manifest stored in the release:

```bash
helm install myvalue clarus-chart
helm get manifest myvalue
helm uninstall myvalue
```

Override a value for a single installation:

```bash
helm install --debug --dry-run setflag clarus-chart --set course=AWS
```

The override applies to that Helm command; it does not modify the chart's `values.yaml`.

## 7. Built-in objects and template functions

Helm templates expose built-in objects. Two commonly used values are:

- `.Release.Name`: the name assigned to this release.
- `.Release.Namespace`: the Kubernetes namespace in which the release is installed.

Update `clarus-chart/values.yaml`:

```yaml
course: DevOps
lesson:
  topic: helm
```

Update `clarus-chart/templates/configmap.yaml`:

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: {{ .Release.Name }}-config
data:
  course: {{ .Values.course | quote }}
  topic: {{ .Values.lesson.topic | upper | quote }}
  namespace: {{ .Release.Namespace | quote }}
  generatedDate: {{ now | date "2006-01-02" | quote }}
```

Preview the output:

```bash
helm install --debug --dry-run builtin-object clarus-chart
```

This example demonstrates:

- `upper` converts text to uppercase.
- `quote` wraps a value in quotes so it is rendered as a YAML string.
- `now` returns the current time.
- `date` formats a date using Go's reference-time layout.

Helm provides functions from Go templates and the Sprig library. See the [template function list](https://helm.sh/docs/chart_template_guide/function_list/) for more.

## 8. Release notes, upgrades, and rollback

Helm can display installation instructions after an install or upgrade. Create `clarus-chart/templates/NOTES.txt`:

```text
Thank you for installing {{ .Chart.Name }}.

Your release is named {{ .Release.Name }}.

Useful commands:

  helm status {{ .Release.Name }}
  helm get all {{ .Release.Name }}
```

Install the chart:

```bash
helm install notes-demo clarus-chart
```

To practice an upgrade, change a value or template and increment the chart's `version` in `clarus-chart/Chart.yaml` (for example, from `0.1.0` to `0.1.1`):

```bash
helm upgrade notes-demo clarus-chart
helm list
helm history notes-demo
```

Helm records revisions for a release. Roll back to revision 1:

```bash
helm rollback notes-demo 1
helm history notes-demo
kubectl describe configmap notes-demo-config
```

Remove the release:

```bash
helm uninstall notes-demo
helm list
```

**Version distinction:** `version` in `Chart.yaml` is the chart package version. `appVersion` describes the application version represented by the chart. A release revision is a separate sequence maintained by Helm when the release changes.

## 9. Host a chart repository with GitHub Pages or static hosting

A classic Helm chart repository is an HTTP(S) endpoint that serves:

- An `index.yaml` metadata file.
- Packaged chart archives (usually `.tgz` files).

A static host such as GitHub Pages can serve these files. This section follows the source exercise's GitHub repository workflow.

### 9.1 Create a repository

Create a GitHub repository, for example `mygithubrepo`, and clone it:

```bash
git clone https://github.com/<github-user>/mygithubrepo.git
cd mygithubrepo
```

If you are starting from an empty local directory instead, initialize Git and configure your identity before committing.

### 9.2 Package a chart

Charts should use semantic versioning. Check `Chart.yaml` and package the chart:

```bash
helm package ../clarus-chart
```

The command creates an archive such as `clarus-chart-0.1.0.tgz`.

### 9.3 Generate repository metadata

Move or copy the archive into the directory that will be published, then generate the index:

```bash
mkdir -p charts
mv clarus-chart-0.1.0.tgz charts/
helm repo index charts --url https://<github-user>.github.io/mygithubrepo/charts
```

The generated `charts/index.yaml` contains chart metadata and URLs. Ensure the URL matches the actual public location where the archive will be served.

A typical layout is:

```text
mygithubrepo/
└── charts/
    ├── index.yaml
    └── clarus-chart-0.1.0.tgz
```

Commit and push the published files:

```bash
git add charts/
git commit -m "Publish clarus-chart 0.1.0"
git push
```

Configure GitHub Pages for the branch/folder containing the static files. Once published, add the repository to Helm:

```bash
helm repo add my-github-repo \
  https://<github-user>.github.io/mygithubrepo/charts
helm repo update
helm repo list
helm search repo my-github-repo
```

Install a chart from the repository:

```bash
helm install github-repo-release my-github-repo/clarus-chart
helm list
kubectl get deployments
kubectl get services
```

Uninstall and remove the repository entry:

```bash
helm uninstall github-repo-release
helm repo remove my-github-repo
helm repo list
```

### 9.4 Publish a new chart version

Update the chart's `version` in `Chart.yaml`, package the new version, and regenerate the index while retaining the existing archive:

```bash
helm package ../clarus-chart --destination charts/
helm repo index charts --url https://<github-user>.github.io/mygithubrepo/charts
git add charts/
git commit -m "Publish updated clarus-chart"
git push
```

Refresh the local repository cache:

```bash
helm repo update
helm search repo my-github-repo --versions
```

> **Important:** GitHub Pages is static hosting. Publishing a chart means committing the packaged archive and updated `index.yaml`; it is not the same as uploading a chart to a ChartMuseum API. For a ChartMuseum server workflow, see [Helm-Chart-Museum](../Helm-Chart-Museum/README.md).

## 10. Cleanup

Remove any remaining practice releases and repository entries:

```bash
helm list --all-namespaces
helm uninstall <release-name> --namespace <namespace>
helm repo remove <repository-name>
```

Only run uninstall commands for releases created during this lab. Verify the namespace and release name before deleting resources.

## Further reading

- [Helm documentation](https://helm.sh/docs/)
- [Helm charts](https://helm.sh/docs/topics/charts/)
- [Chart templates](https://helm.sh/docs/chart_template_guide/)
- [Chart repositories](https://helm.sh/docs/topics/chart_repository/)
- [Artifact Hub](https://artifacthub.io/)
- [Semantic Versioning](https://semver.org/)

---

*This guide is an educational lab. Validate chart values, security settings, Kubernetes compatibility, and deployment behavior in a non-production cluster before adopting a chart in production.*
