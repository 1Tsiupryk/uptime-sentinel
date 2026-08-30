import { useEffect, useState } from "react"

import {
  deleteMonitor,
  getMonitors,
  triggerCheck,
  updateMonitor,
} from "./api/client"
import { MonitorForm } from "./components/MonitorForm"
import { MonitorList } from "./components/MonitorList"
import sentinelIcon from "./assets/icon.png"
import type { CheckResult, Monitor } from "./types/monitor"

import "./App.css"

function App() {
  const [monitors, setMonitors] = useState<Monitor[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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

  useEffect(() => {
    async function loadMonitors() {
      try {
        setError(null)
        setMonitors(await getMonitors())
      } catch (error) {
        setError(
          error instanceof Error
            ? error.message
            : "Failed to load monitors",
        )
      } finally {
        setIsLoading(false)
      }
    }

    void loadMonitors()
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
    } catch (error) {
      setCheckError({
        monitorId,
        message:
          error instanceof Error
            ? error.message
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

      setLatestChecks((current) => {
        const updatedChecks = { ...current }
        delete updatedChecks[monitor.id]
        return updatedChecks
      })
    } catch (error) {
      setDeleteError({
        monitorId: monitor.id,
        message:
          error instanceof Error
            ? error.message
            : "Failed to delete monitor",
      })
    } finally {
      setDeletingMonitorId(null)
    }
  }

  async function handleToggleEnabled(monitor: Monitor) {
    if (
      checkingMonitorId !== null ||
      deletingMonitorId !== null ||
      updatingMonitorId !== null
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
    } catch (error) {
      setUpdateError({
        monitorId: monitor.id,
        message:
          error instanceof Error
            ? error.message
            : "Failed to update monitor",
      })
    } finally {
      setUpdatingMonitorId(null)
    }
  }

  return (
    <main className="app-shell">
      <header className="app-header">
        <div className="brand">
          <img
            className="brand-icon"
            src={sentinelIcon}
            alt=""
            aria-hidden="true"
          />
          <h1>Uptime Sentinel</h1>
        </div>

        <div className="monitor-counter">
          <strong>{monitors.length}</strong>
          <span>monitors</span>
        </div>
      </header>

      <div className="dashboard-grid">
        <MonitorForm
          onCreated={(monitor) => {
            setMonitors((current) => [
              monitor,
              ...current,
            ])
          }}
        />

        <div className="content-column">
          {isLoading && (
            <p className="state-message">
              Loading monitors...
            </p>
          )}

          {error && (
            <p className="alert" role="alert">
              Failed to load monitors: {error}
            </p>
          )}

          {!isLoading && !error && (
            <MonitorList
              monitors={monitors}
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
    </main>
  )
}

export default App
