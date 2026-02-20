{{/*
Chart name
*/}}
{{- define "todo-app.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Fully qualified app name (release-prefixed)
*/}}
{{- define "todo-app.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Chart label
*/}}
{{- define "todo-app.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Standard labels
*/}}
{{- define "todo-app.labels" -}}
helm.sh/chart: {{ include "todo-app.chart" . }}
{{ include "todo-app.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "todo-app.selectorLabels" -}}
app.kubernetes.io/name: {{ include "todo-app.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Component-specific fullnames
*/}}
{{- define "todo-app.frontend.fullname" -}}
{{- printf "%s-frontend" (include "todo-app.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "todo-app.backend.fullname" -}}
{{- printf "%s-backend" (include "todo-app.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{- define "todo-app.mcp.fullname" -}}
{{- printf "%s-mcp" (include "todo-app.fullname" .) | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
imagePullSecrets block — emits nothing when list is empty (local dev)
*/}}
{{- define "todo-app.imagePullSecrets" -}}
{{- with .Values.global.imagePullSecrets }}
imagePullSecrets:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}

{{/*
Effective secret name — uses existingSecretName when set (cloud), otherwise chart-managed
*/}}
{{- define "todo-app.secretName" -}}
{{- if .Values.secrets.existingSecretName -}}
{{ .Values.secrets.existingSecretName }}
{{- else -}}
{{ include "todo-app.fullname" . }}-secret
{{- end }}
{{- end }}

{{/*
Effective image tag — global.imageTag overrides per-service .image.tag (set by CI)
*/}}
{{- define "todo-app.imageTag" -}}
{{- .Values.global.imageTag | default "latest" }}
{{- end }}
