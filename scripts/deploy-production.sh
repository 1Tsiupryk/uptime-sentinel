#!/usr/bin/env bash

set -Eeuo pipefail

trap 'echo "Deployment failed at line $LINENO"' ERR

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
cd "$PROJECT_ROOT"

NAMESPACE="uptime-sentinel"
INFRA_OVERLAY="infra/kubernetes/overlays/production/infrastructure"
MIGRATION_OVERLAY="infra/kubernetes/overlays/production/migration"
APPLICATION_OVERLAY="infra/kubernetes/overlays/production/application"

command -v kubectl >/dev/null
test -f "$INFRA_OVERLAY/.env"

EXPECTED_CONTEXT="${KUBE_CONTEXT:?Set KUBE_CONTEXT before deployment}"
CURRENT_CONTEXT="$(kubectl config current-context)"

if [[ "$CURRENT_CONTEXT" != "$EXPECTED_CONTEXT" ]]; then
    echo "Expected context: $EXPECTED_CONTEXT"
    echo "Current context:  $CURRENT_CONTEXT"
    exit 1
fi

KUBECTL=(kubectl --context "$EXPECTED_CONTEXT")

echo "====================================================================="
echo "Deploying infrastructure..."
echo "====================================================================="
"${KUBECTL[@]}" apply -k "$INFRA_OVERLAY"
"${KUBECTL[@]}" rollout status statefulset/postgres -n "$NAMESPACE" --timeout=120s
"${KUBECTL[@]}" rollout status deployment/redis -n "$NAMESPACE" --timeout=120s

echo "====================================================================="
echo "Deploying migration..."
echo "====================================================================="
"${KUBECTL[@]}" delete job migration-job -n "$NAMESPACE" --ignore-not-found
"${KUBECTL[@]}" apply -k "$MIGRATION_OVERLAY"
if ! "${KUBECTL[@]}" wait --for=condition=complete job/migration-job -n "$NAMESPACE" --timeout=120s; then
    echo "====================================================================="
    echo "Migration failed or timed out"
    echo "Logs for migration-job:"
    "${KUBECTL[@]}" logs --namespace "$NAMESPACE" job/migration-job || true
    "${KUBECTL[@]}" describe job --namespace "$NAMESPACE" migration-job || true
    exit 1
fi

echo "====================================================================="
echo "Migration completed successfully"
echo "Logs for migration-job:"
"${KUBECTL[@]}" logs -n "$NAMESPACE" job/migration-job

echo "====================================================================="
echo "Deploying application..."
echo "====================================================================="
"${KUBECTL[@]}" apply -k "$APPLICATION_OVERLAY"
"${KUBECTL[@]}" rollout status deployment/backend -n "$NAMESPACE" --timeout=120s
"${KUBECTL[@]}" rollout status deployment/worker -n "$NAMESPACE" --timeout=120s
"${KUBECTL[@]}" rollout status deployment/frontend -n "$NAMESPACE" --timeout=120s

echo "====================================================================="
echo "Command to access the application:"
echo "kubectl port-forward -n traefik service/traefik 8080:80"
echo "http://localhost:8080"
echo "====================================================================="