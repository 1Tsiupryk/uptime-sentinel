import { useCallback, useEffect, useState } from "react"
import {
  BrowserRouter,
  Link,
  Navigate,
  NavLink,
  Route,
  Routes,
} from "react-router-dom"

import {
  deleteMonitor,
  getIncidents,
  getMonitors,
  triggerCheck,
  updateMonitor,
} from "./api/client"
import sentinelIcon from "./assets/icon.png"
import { MonitorForm } from "./components/MonitorForm"
import { MonitorList } from "./components/MonitorList"
import { IncidentsPage } from "./pages/IncidentsPage"
import type { Incident } from "./types/incident"
import type { CheckResult, Monitor } from "./types/monitor"
import { INCIDENT_POLL_INTERVAL_MS } from "./utils/incidents"

import "./App.css"


function UptimeSentinelApp() {
  const [monitors, setMonitors] = useState<Monitor[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [activeIncidents, setActiveIncidents] = useState<Incident[]>([])
  const [incidentError, setIncidentError] = useState<string | null>(null)

  const [latestChecks, setLatestChecks] = useState<
    Record<number, CheckResult>
  >({})

  const [checkingMonitorId, setCheckingMonitorId] =
    useState<number | null>(null)

  const [checkError, setCheckError] = useState<{
    monitorId: number
    message: string
  } | null>(null)

  const [deletingMonitorId, setDeletingMonitorId] = useState<number | null>(null)

  const [deleteError, setDeleteError] = useState<{
    monitorId: number
    message: string
  } | null>(null)

  const [updatingMonitorId, setUpdatingMonitorId] =
    useState<number | null>(null)

  const [updateError, setUpdateError] = useState<{
    monitorId: number
    message: string
  } | null>(null)

  const refreshActiveIncidents = useCallback(async () => {
    try {
      const loadedIncidents = await getIncidents("open")
      setIncidentError(null)
      setActiveIncidents(loadedIncidents)
    } catch (loadError) {
      setIncidentError(
        loadError instanceof Error
          ? loadError.message
          : "Failed to load incidents",
      )
    }
  }, [])

  useEffect(() => {
    let cancelled = false

    async function loadMonitors() {
      try {
        const loadedMonitors = await getMonitors()

        if (!cancelled) {
          setError(null)
          setMonitors(loadedMonitors)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load monitors",
          )
        }
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }

    async function loadActiveIncidents() {
      try {
        const loadedIncidents = await getIncidents("open")

        if (!cancelled) {
          setIncidentError(null)
          setActiveIncidents(loadedIncidents)
        }
      } catch (loadError) {
        if (!cancelled) {
          setIncidentError(
            loadError instanceof Error
              ? loadError.message
              : "Failed to load incidents",
          )
        }
      }
    }

    void loadMonitors()
    void loadActiveIncidents()

    const intervalId = window.setInterval(() => {
      void loadActiveIncidents()
    }, INCIDENT_POLL_INTERVAL_MS)

    return () => {
      cancelled = true
      window.clearInterval(intervalId)
    }
  }, [])

  async function handleCheck(monitorId: number) {
    if (checkingMonitorId !== null) {
      return
    }

    try {
      setCheckingMonitorId(monitorId)
      setCheckError(null)

      const result = await triggerCheck(monitorId)

      setLatestChecks((current) => ({
        ...current,
        [monitorId]: result,
      }))
      void refreshActiveIncidents()
    } catch (checkFailure) {
      setCheckError({
        monitorId,
        message:
          checkFailure instanceof Error
            ? checkFailure.message
            : "Failed to check monitor",
      })
    } finally {
      setCheckingMonitorId(null)
    }
  }

  async function handleDelete(monitor: Monitor) {
    const confirmed = window.confirm(
      `Delete monitor "${monitor.name}" and its check history?`,
    )

    if (!confirmed) {
      return
    }

    try {
      setDeletingMonitorId(monitor.id)
      setDeleteError(null)

      await deleteMonitor(monitor.id)

      setMonitors((current) =>
        current.filter((item) => item.id !== monitor.id),
      )
      setActiveIncidents((current) =>
        current.filter((incident) => incident.monitor_id !== monitor.id),
      )
      setLatestChecks((current) => {
        const updatedChecks = { ...current }
        delete updatedChecks[monitor.id]
        return updatedChecks
      })
    } catch (deleteFailure) {
      setDeleteError({
        monitorId: monitor.id,
        message:
          deleteFailure instanceof Error
            ? deleteFailure.message
            : "Failed to delete monitor",
      })
    } finally {
      setDeletingMonitorId(null)
    }
  }

  async function handleToggleEnabled(monitor: Monitor) {
    if (
      checkingMonitorId !== null
      || deletingMonitorId !== null
      || updatingMonitorId !== null
    ) {
      return
    }

    try {
      setUpdatingMonitorId(monitor.id)
      setUpdateError(null)

      const updatedMonitor = await updateMonitor(monitor.id, {
        enabled: !monitor.enabled,
      })

      setMonitors((current) =>
        current.map((item) =>
          item.id === updatedMonitor.id ? updatedMonitor : item,
        ),
      )
    } catch (updateFailure) {
      setUpdateError({
        monitorId: monitor.id,
        message:
          updateFailure instanceof Error
            ? updateFailure.message
            : "Failed to update monitor",
      })
    } finally {
      setUpdatingMonitorId(null)
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <Link className="brand" to="/">
          <img
            className="brand-icon"
            src={sentinelIcon}
            alt=""
            aria-hidden="true"
          />
          <h1>Uptime Sentinel</h1>
        </Link>

        <nav className="primary-nav" aria-label="Primary navigation">
          <NavLink end to="/">
            Dashboard
          </NavLink>
          <NavLink to="/incidents">
            Incidents
          </NavLink>
        </nav>

        <div className="header-metrics">
          <Link
            className={`incident-counter ${
              activeIncidents.length > 0 ? "has-active" : ""
            }`}
            to="/incidents"
            aria-label={
              incidentError
                ? "Incident status unavailable"
                : `${activeIncidents.length} active ${
                    activeIncidents.length === 1 ? "incident" : "incidents"
                  }`
            }
            title={incidentError ?? undefined}
          >
            <strong>{incidentError ? "—" : activeIncidents.length}</strong>
            <span>
              {activeIncidents.length === 1 ? "incident" : "incidents"}
            </span>
          </Link>

          <div className="monitor-counter">
            <strong>{monitors.length}</strong>
            <span>{monitors.length === 1 ? "monitor" : "monitors"}</span>
          </div>
        </div>
      </header>

      <Routes>
        <Route
          path="/"
          element={
            <div className="dashboard-grid">
              <MonitorForm
                onCreated={(monitor) => {
                  setMonitors((current) => [monitor, ...current])
                }}
              />

              <div className="content-column">
                {isLoading && (
                  <p className="state-message">Loading monitors...</p>
                )}

                {error && (
                  <p className="alert" role="alert">
                    Failed to load monitors: {error}
                  </p>
                )}

                {!isLoading && !error && (
                  <MonitorList
                    monitors={monitors}
                    activeIncidents={activeIncidents}
                    latestChecks={latestChecks}
                    checkingMonitorId={checkingMonitorId}
                    checkError={checkError}
                    deletingMonitorId={deletingMonitorId}
                    deleteError={deleteError}
                    updatingMonitorId={updatingMonitorId}
                    updateError={updateError}
                    onCheck={handleCheck}
                    onDelete={handleDelete}
                    onToggleEnabled={handleToggleEnabled}
                  />
                )}
              </div>
            </div>
          }
        />
        <Route path="/incidents" element={<IncidentsPage monitors={monitors} />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </main>
  )
}

function App() {
  return (
    <BrowserRouter>
      <UptimeSentinelApp />
    </BrowserRouter>
  )
}

export default App
