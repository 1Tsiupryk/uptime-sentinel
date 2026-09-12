#!/usr/bin/env bash

set -Eeuo pipefail

trap 'echo "Deployment failed at line $LINENO"' ERR

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

echo "=================================================================="
echo "Deploying monitoring..."
echo "=================================================================="

helm repo add prometheus-community https://prometheus-community.github.io/helm-charts --force-update

helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
  --version 88.0.1 \
  --values infra/kubernetes/monitoring/values.yml \
  --namespace monitoring \
  --create-namespace \
  --wait \
  --timeout 10m

kubectl apply -k infra/kubernetes/monitoring
kubectl apply -k infra/grafana/dashboards

echo "=================================================================="
echo "Monitoring deployed successfully!"
echo "=================================================================="
echo "Commands to access the monitoring services:"
echo "Prometheus: kubectl port-forward -n monitoring service/monitoring-kube-prometheus-prometheus 9090:9090"
echo "Grafana:    kubectl port-forward -n monitoring service/monitoring-grafana 3002:80"
echo "=================================================================="
