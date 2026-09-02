import { useEffect, useMemo, useState } from "react"

import { getIncidents } from "../api/client"
import { IncidentDetailsModal } from "../components/IncidentDetailsModal"
import {
  SortDropdown,
  type IncidentSort,
} from "../components/SortDropdown"
import type { Incident, IncidentStatus } from "../types/incident"
import type { Monitor } from "../types/monitor"
import {
  formatIncidentDuration,
  getIncidentDurationMs,
  INCIDENT_POLL_INTERVAL_MS,
} from "../utils/incidents"


type IncidentFilter = "all" | IncidentStatus
interface IncidentsPageProps {
  monitors: Monitor[]
}

export function IncidentsPage({ monitors }: IncidentsPageProps) {
  const [incidents, setIncidents] = useState<Incident[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [filter, setFilter] = useState<IncidentFilter>("all")
  const [sort, setSort] = useState<IncidentSort>("newest")
  const [selectedIncidentId, setSelectedIncidentId] = useState<number | null>(null)
  const [durationReference, setDurationReference] = useState(Date.now)

  useEffect(() => {
    let cancelled = false

    async function loadIncidents(showLoading: boolean) {
      try {
        if (showLoading) {
          setIsLoading(true)
        }

        const loadedIncidents = await getIncidents()

        if (!cancelled) {
          setError(null)
          setIncidents(loadedIncidents)
          setDurationReference(Date.now())
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load incidents",
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
  }, [])

  const monitorNames = useMemo(
    () => new Map(monitors.map((monitor) => [monitor.id, monitor.name])),
    [monitors],
  )

  const visibleIncidents = useMemo(() => {
    const filtered = incidents.filter((incident) => {
      if (filter === "open") {
        return incident.resolved_at === null
      }

      if (filter === "resolved") {
        return incident.resolved_at !== null
      }

      return true
    })

    return [...filtered].sort((first, second) => {
      if (sort === "oldest") {
        return new Date(first.started_at).getTime()
          - new Date(second.started_at).getTime()
      }

      if (sort === "longest" || sort === "shortest") {
        const difference = getIncidentDurationMs(second, durationReference)
          - getIncidentDurationMs(first, durationReference)

        return sort === "longest" ? difference : -difference
      }

      if (sort === "monitor") {
        const firstName = monitorNames.get(first.monitor_id) ?? ""
        const secondName = monitorNames.get(second.monitor_id) ?? ""
        return firstName.localeCompare(secondName)
      }

      return new Date(second.started_at).getTime()
        - new Date(first.started_at).getTime()
    })
  }, [durationReference, filter, incidents, monitorNames, sort])

  const activeCount = incidents.filter(
    (incident) => incident.resolved_at === null,
  ).length
  const resolvedCount = incidents.length - activeCount

  return (
    <section className="incidents-page">
      <header className="page-heading">
        <div>
          <span className="eyebrow">Operational history</span>
          <h2>Incidents</h2>
          <p>Outage history across all monitored endpoints.</p>
        </div>
      </header>

      <div className="incident-summary" aria-label="Incident summary">
        <article className="summary-card active">
          <span>Active</span>
          <strong>{activeCount}</strong>
        </article>
        <article className="summary-card resolved">
          <span>Resolved</span>
          <strong>{resolvedCount}</strong>
        </article>
        <article className="summary-card">
          <span>Total</span>
          <strong>{incidents.length}</strong>
        </article>
      </div>

      <section className="panel incidents-panel">
        <div className="incident-toolbar">
          <div className="incident-filters" aria-label="Filter incidents">
            {(["all", "open", "resolved"] as const).map((value) => (
              <button
                className={filter === value ? "active" : ""}
                type="button"
                aria-pressed={filter === value}
                key={value}
                onClick={() => setFilter(value)}
              >
                {value === "open"
                  ? "Active"
                  : value[0].toUpperCase() + value.slice(1)}
              </button>
            ))}
          </div>

          <div className="sort-control">
            <span>Sort</span>
            <SortDropdown
              value={sort}
              onChange={setSort}
            />
          </div>
        </div>

        {isLoading && <p className="state-message">Loading incidents...</p>}

        {error && (
          <p className="alert" role="alert">
            Failed to load incidents: {error}
          </p>
        )}

        {!isLoading && !error && visibleIncidents.length === 0 && (
          <div className="empty-state">
            <strong>No incidents found</strong>
            <p>The selected filter has no matching incidents.</p>
          </div>
        )}

        {!isLoading && !error && visibleIncidents.length > 0 && (
          <div className="incident-table-wrapper">
            <table className="incident-table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Monitor</th>
                  <th>Started</th>
                  <th>Resolved</th>
                  <th>Duration</th>
                  <th>ID</th>
                  <th><span className="visually-hidden">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                {visibleIncidents.map((incident) => {
                  const isResolved = incident.resolved_at !== null

                  return (
                    <tr key={incident.id}>
                      <td>
                        <span
                          className={`incident-state ${
                            isResolved ? "resolved" : "active"
                          }`}
                        >
                          <span className="status-dot" />
                          {isResolved ? "Resolved" : "Active"}
                        </span>
                      </td>
                      <td className="incident-monitor-name">
                        {monitorNames.get(incident.monitor_id)
                          ?? `Monitor #${incident.monitor_id}`}
                      </td>
                      <td>{new Date(incident.started_at).toLocaleString()}</td>
                      <td>
                        {incident.resolved_at
                          ? new Date(incident.resolved_at).toLocaleString()
                          : "—"}
                      </td>
                      <td>{formatIncidentDuration(incident)}</td>
                      <td>#{incident.id}</td>
                      <td>
                        <button
                          className="table-action"
                          type="button"
                          onClick={() => setSelectedIncidentId(incident.id)}
                        >
                          Details
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>

      {selectedIncidentId !== null && (
        <IncidentDetailsModal
          incidentId={selectedIncidentId}
          monitors={monitors}
          onClose={() => setSelectedIncidentId(null)}
        />
      )}
    </section>
  )
}
