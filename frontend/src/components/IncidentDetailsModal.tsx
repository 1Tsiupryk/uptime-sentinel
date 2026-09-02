import { useEffect, useState } from "react"

import { getIncident } from "../api/client"
import type { Incident } from "../types/incident"
import type { Monitor } from "../types/monitor"
import { formatIncidentDuration } from "../utils/incidents"


interface IncidentDetailsModalProps {
  incidentId: number
  monitors: Monitor[]
  onClose: () => void
}

export function IncidentDetailsModal({
  incidentId,
  monitors,
  onClose,
}: IncidentDetailsModalProps) {
  const [incident, setIncident] = useState<Incident | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadIncident() {
      try {
        setIsLoading(true)
        setError(null)
        const loadedIncident = await getIncident(incidentId)

        if (!cancelled) {
          setIncident(loadedIncident)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load incident",
          )
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadIncident()

    return () => {
      cancelled = true
    }
  }, [incidentId])

  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose()
      }
    }

    document.addEventListener("keydown", handleKeyDown)
    return () => document.removeEventListener("keydown", handleKeyDown)
  }, [onClose])

  const monitor = incident
    ? monitors.find((item) => item.id === incident.monitor_id)
    : null

  return (
    <div
      className="modal-backdrop"
      role="presentation"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) {
          onClose()
        }
      }}
    >
      <section
        className="incident-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="incident-modal-title"
      >
        <header className="incident-modal-header">
          <div>
            <span className="eyebrow">Incident details</span>
            <h2 id="incident-modal-title">Incident #{incidentId}</h2>
          </div>

          <button
            className="modal-close"
            type="button"
            aria-label="Close incident details"
            onClick={onClose}
          >
            ×
          </button>
        </header>

        {isLoading && <p className="history-message">Loading incident...</p>}

        {error && (
          <p className="alert" role="alert">
            {error}
          </p>
        )}

        {incident && !isLoading && (
          <dl className="incident-detail-list">
            <div>
              <dt>Status</dt>
              <dd
                className={
                  incident.resolved_at
                    ? "incident-state resolved"
                    : "incident-state active"
                }
              >
                {incident.resolved_at ? "Resolved" : "Active"}
              </dd>
            </div>
            <div>
              <dt>Monitor</dt>
              <dd>{monitor?.name ?? `Monitor #${incident.monitor_id}`}</dd>
            </div>
            <div>
              <dt>Started</dt>
              <dd>{new Date(incident.started_at).toLocaleString()}</dd>
            </div>
            <div>
              <dt>Resolved</dt>
              <dd>
                {incident.resolved_at
                  ? new Date(incident.resolved_at).toLocaleString()
                  : "—"}
              </dd>
            </div>
            <div>
              <dt>Duration</dt>
              <dd>{formatIncidentDuration(incident)}</dd>
            </div>
            <div>
              <dt>Opening check</dt>
              <dd>#{incident.opening_check_id}</dd>
            </div>
            <div>
              <dt>Closing check</dt>
              <dd>
                {incident.closing_check_id
                  ? `#${incident.closing_check_id}`
                  : "—"}
              </dd>
            </div>
          </dl>
        )}
      </section>
    </div>
  )
}
