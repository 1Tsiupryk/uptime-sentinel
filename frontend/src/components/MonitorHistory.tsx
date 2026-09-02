import { useState } from "react"

import { CheckHistory } from "./CheckHistory"
import { IncidentHistory } from "./IncidentHistory"


interface MonitorHistoryProps {
  monitorId: number
  refreshKey?: number
}

export function MonitorHistory({
  monitorId,
  refreshKey,
}: MonitorHistoryProps) {
  const [activeTab, setActiveTab] = useState<"checks" | "incidents">("checks")

  return (
    <div className="monitor-history">
      <div className="history-tabs" role="tablist" aria-label="Monitor history">
        <button
          className={activeTab === "checks" ? "active" : ""}
          type="button"
          role="tab"
          aria-selected={activeTab === "checks"}
          onClick={() => setActiveTab("checks")}
        >
          Checks
        </button>
        <button
          className={activeTab === "incidents" ? "active" : ""}
          type="button"
          role="tab"
          aria-selected={activeTab === "incidents"}
          onClick={() => setActiveTab("incidents")}
        >
          Incidents
        </button>
      </div>

      <div role="tabpanel">
        {activeTab === "checks" ? (
          <CheckHistory monitorId={monitorId} refreshKey={refreshKey} />
        ) : (
          <IncidentHistory monitorId={monitorId} refreshKey={refreshKey} />
        )}
      </div>
    </div>
  )
}
