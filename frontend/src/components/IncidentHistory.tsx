import { useEffect, useState } from "react"

import { getMonitorIncidents } from "../api/client"
import type { Incident } from "../types/incident"
import {
  formatIncidentDuration,
  INCIDENT_POLL_INTERVAL_MS,
} from "../utils/incidents"


interface IncidentHistoryProps {
  monitorId: number
  refreshKey?: number
}

export function IncidentHistory({
  monitorId,
  refreshKey,
}: IncidentHistoryProps) {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadIncidents(showLoading: boolean) {
      try {
        if (showLoading) {
          setIsLoading(true)
        }

        const loadedIncidents = await getMonitorIncidents(monitorId)

        if (!cancelled) {
          setError(null)
          setIncidents(loadedIncidents)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load incident history",
          )
        }
      } finally {
        if (showLoading && !cancelled) {
          setIsLoading(false)
        }
      }
    }

    void loadIncidents(true)

    const intervalId = window.setInterval(() => {
      void loadIncidents(false)
    }, INCIDENT_POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [monitorId, refreshKey])

  return (
    <div className="check-history incident-history">
      <h4>Incident history</h4>

      {isLoading && (
        <p className="history-message">Loading incidents...</p>
      )}

      {error && (
        <p className="alert check-error" role="alert">
          {error}
        </p>
      )}

      {!isLoading && !error && incidents.length === 0 && (
        <p className="history-message">No incidents recorded yet.</p>
      )}

      {!isLoading && !error && incidents.length > 0 && (
        <ul className="history-list">
          {incidents.map((incident) => {
            const isResolved = incident.resolved_at !== null

            return (
              <li
                className={`history-item incident-history-item ${
                  isResolved ? "resolved" : "active"
                }`}
                key={incident.id}
              >
                <div className="history-item-header">
                  <strong>{isResolved ? "Resolved" : "Active"}</strong>
                  <time dateTime={incident.started_at}>
                    {new Date(incident.started_at).toLocaleString()}
                  </time>
                </div>

                <div className="history-details">
                  <span>{formatIncidentDuration(incident)}</span>
                  <span>Incident #{incident.id}</span>
                </div>

                <div className="history-details">
                  <span>Opened by check #{incident.opening_check_id}</span>
                  <span>
                    {incident.closing_check_id
                      ? `Closed by #${incident.closing_check_id}`
                      : "Ongoing"}
                  </span>
                </div>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
