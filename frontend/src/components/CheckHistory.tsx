import { useEffect, useState } from "react"

import { getMonitorChecks } from "../api/client"
import type { CheckResult } from "../types/monitor"

interface CheckHistoryProps {
    monitorId: number
    refreshKey?: number
}

export function CheckHistory({
    monitorId,
    refreshKey,
}: CheckHistoryProps) {
    const [checks, setChecks] = useState<CheckResult[]>([])
    const [isLoading, setIsLoading] = useState(true)
    const [error, setError] = useState<string | null>(null)

    useEffect(() => {
        let cancelled = false

        async function loadChecks() {
            try {
                setIsLoading(true)
                setError(null)

                const loadedChecks =
                    await getMonitorChecks(monitorId)

                if (!cancelled) {
                    setChecks(loadedChecks)
                }
            } catch (error) {
                if (!cancelled) {
                    setError(
                        error instanceof Error
                            ? error.message
                            : "Failed to load check history",
                    )
                }
            } finally {
                if (!cancelled) {
                    setIsLoading(false)
                }
            }
        }

        void loadChecks()

        return () => {
            cancelled = true
        }
    }, [monitorId, refreshKey])

    if (isLoading) {
        return (
            <div className="check-history">
                <p className="history-message">
                    Loading history...
                </p>
            </div>
        )
    }

    if (error) {
        return (
            <div className="check-history">
                <p className="alert check-error" role="alert">
                    {error}
                </p>
            </div>
        )
    }

    return (
        <div className="check-history">
            <h4>Check history</h4>

            {checks.length === 0 ? (
                <p className="history-message">
                    No checks recorded yet.
                </p>
            ) : (
                <ul className="history-list">
                    {checks.map((check) => (
                        <li
                            className={`history-item ${check.status}`}
                            key={check.id}
                        >
                            <div className="history-item-header">
                                <strong>
                                    {check.status.toUpperCase()}
                                </strong>

                                <time dateTime={check.checked_at}>
                                    {new Date(
                                        check.checked_at,
                                    ).toLocaleString()}
                                </time>
                            </div>

                            <div className="history-details">
                                <span>
                                    HTTP {check.status_code ?? "—"}
                                </span>

                                <span>{check.latency_ms} ms</span>
                            </div>

                            {check.error && (
                                <p className="history-error">
                                    {check.error}
                                </p>
                            )}
                        </li>
                    ))}
                </ul>
            )}
        </div>
    )
}