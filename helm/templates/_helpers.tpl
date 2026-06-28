{{/*
    Expand the name of the chart.
*/}}

{{- define "cpaor-data-viz-dashboard-helm.name" -}}
    {{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
    Create a default fully qualified app name.
    We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
    If release name contains chart name it will be used as a full name.
*/}}

{{- define "cpaor-data-viz-dashboard-helm.fullname" -}}
    {{- if .Values.fullnameOverride -}}
        {{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
    {{- else -}}
        {{- $name := default .Chart.Name .Values.nameOverride -}}
        {{- if contains $name .Release.Name -}}
            {{- .Release.Name | trunc 63 | trimSuffix "-" -}}
        {{- else -}}
            {{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" -}}
        {{- end -}}
    {{- end -}}
{{- end -}}

{{/*
    Create chart name and version as used by the chart label.
*/}}

{{- define "cpaor-data-viz-dashboard-helm.chart" -}}
    {{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{/*
    Render the `env:` entries for a workload (explicit env lane; always wins over envFrom).
    Order (later wins): APP_ENVIRONMENT (global ConfigMap) -> plain `env:` values -> external secret `env` mappings.
    Usage: include "cpaor-data-viz-dashboard-helm.workloadEnv" (dict "configName" <cm-name> "workload" .Values.streamlit)
*/}}

{{- define "cpaor-data-viz-dashboard-helm.workloadEnv" -}}
    {{- $w := .workload -}}
- name: APP_ENVIRONMENT
  valueFrom:
    configMapKeyRef:
      name: {{ .configName }}
      key: APP_ENVIRONMENT
    {{- range $k, $v := $w.env }}
- name: {{ $k }}
  value: {{ $v | quote }}
    {{- end }}
    {{- if $w.externalSecrets }}
    {{- range $w.externalSecrets.env }}
- name: {{ .name }}
  valueFrom:
    secretKeyRef:
      name: {{ .secretName }}
      key: {{ .secretKey }}
    {{- end }}
    {{- end }}
{{- end -}}

{{/*
    Render the `envFrom:` entries for a workload (bulk lane; overridden by any `env:` key).
    Order (later wins): chart-managed inline Secret -> external secret `envFrom` bulk imports.
    Emits nothing when there are no sources, so callers must guard the `envFrom:` key.
    Usage: include "cpaor-data-viz-dashboard-helm.workloadEnvFrom" (dict "secretName" <secret-name> "workload" .Values.streamlit)
*/}}

{{- define "cpaor-data-viz-dashboard-helm.workloadEnvFrom" -}}
    {{- $w := .workload -}}
    {{- $hasInline := false -}}
    {{- range $k, $v := $w.secrets }}
    {{- if $v }}{{- $hasInline = true }}{{- end }}
    {{- end }}
    {{- if $hasInline }}
- secretRef:
    name: {{ .secretName }}
    {{- end }}
    {{- if $w.externalSecrets }}
    {{- range $w.externalSecrets.envFrom }}
- secretRef:
    name: {{ . }}
    {{- end }}
    {{- end }}
{{- end -}}
