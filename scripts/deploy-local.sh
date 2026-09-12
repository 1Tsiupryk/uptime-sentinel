#!/usr/bin/env bash

set -Eeuo pipefail

trap 'echo "Deployment failed at line $LINENO"' ERR

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

NAMESPACE="uptime-sentinel"
INFRA_OVERLAY="infra/kubernetes/overlays/local/infrastructure"
MIGRATION_OVERLAY="infra/kubernetes/overlays/local/migration"
APPLICATION_OVERLAY="infra/kubernetes/overlays/local/application"

echo "====================================================================="
echo "Deploying infrastructure..."
echo "====================================================================="
kubectl apply -k "$INFRA_OVERLAY"
kubectl rollout status statefulset/postgres -n "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/redis -n "$NAMESPACE" --timeout=120s

echo "====================================================================="
echo "Deploying migration..."
echo "====================================================================="
kubectl delete job migration-job -n "$NAMESPACE" --ignore-not-found
kubectl apply -k "$MIGRATION_OVERLAY"
if ! kubectl wait --for=condition=complete job/migration-job -n "$NAMESPACE" --timeout=120s; then
    echo "====================================================================="
    echo "Migration failed or timed out"
    echo "Logs for migration-job:"
    kubectl logs --namespace "$NAMESPACE" job/migration-job || true
    kubectl describe job --namespace "$NAMESPACE" migration-job || true
    exit 1
fi

echo "====================================================================="
echo "Migration completed successfully"
echo "Logs for migration-job:"
kubectl logs -n "$NAMESPACE" job/migration-job

echo "====================================================================="
echo "Deploying application..."
echo "====================================================================="
kubectl apply -k "$APPLICATION_OVERLAY"
kubectl rollout restart deployment/backend deployment/worker deployment/frontend -n "$NAMESPACE"
kubectl rollout status deployment/backend -n "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/worker -n "$NAMESPACE" --timeout=120s
kubectl rollout status deployment/frontend -n "$NAMESPACE" --timeout=120s

echo "====================================================================="
echo "Command to access the application:"
echo "kubectl port-forward -n traefik service/traefik 8080:80"
echo "http://localhost:8080"
echo "====================================================================="