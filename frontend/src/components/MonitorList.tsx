import { useState } from "react"

import { CheckHistory } from "./CheckHistory"
import type {
    CheckResult,
    Monitor,
} from "../types/monitor"

function PulseIcon() {
    return (
        <svg className="button-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M3 12h4l2-7 4 14 2-7h6" />
        </svg>
    )
}

function ClockIcon() {
    return (
        <svg className="button-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7v5l3 2" />
        </svg>
    )
}

function ToggleIcon({ enabled }: { enabled: boolean }) {
    return (
        <svg className="button-icon" viewBox="0 0 24 24" aria-hidden="true">
            <circle cx="12" cy="12" r="9" />
            {enabled ? (
                <>
                    <path d="M10 9v6" />
                    <path d="M14 9v6" />
                </>
            ) : (
                <path d="m10 8 6 4-6 4Z" />
            )}
        </svg>
    )
}

function TrashIcon() {
    return (
        <svg className="button-icon" viewBox="0 0 24 24" aria-hidden="true">
            <path d="M4 7h16" />
            <path d="M9 7V4h6v3" />
            <path d="m6 7 1 13h10l1-13" />
            <path d="M10 11v5M14 11v5" />
        </svg>
    )
}

interface MonitorListProps {
    monitors: Monitor[]
    latestChecks: Record<number, CheckResult>
    checkingMonitorId: number | null
    checkError: {
        monitorId: number
        message: string
    } | null
    deletingMonitorId: number | null
    deleteError: {
        monitorId: number
        message: string
    } | null
    updatingMonitorId: number | null
    updateError: {
        monitorId: number
        message: string
    } | null
    onCheck: (monitorId: number) => Promise<void>
    onDelete: (monitor: Monitor) => Promise<void>
    onToggleEnabled: (monitor: Monitor) => Promise<void>
}

export function MonitorList({
    monitors,
    latestChecks,
    checkingMonitorId,
    checkError,
    deletingMonitorId,
    deleteError,
    updatingMonitorId,
    updateError,
    onCheck,
    onDelete,
    onToggleEnabled,
}: MonitorListProps) {
    const [historyMonitorId, setHistoryMonitorId] =
        useState<number | null>(null)

    return (
        <section className="panel monitor-section">
            <header className="section-heading section-heading-row">
                <div>
                    <span className="eyebrow">Infrastructure</span>
                    <h2>Monitors</h2>
                </div>
            </header>

            {monitors.length === 0 ? (
                <div className="empty-state">
                    <strong>No monitors yet</strong>
                    <p>Add your first endpoint using the form.</p>
                </div>
            ) : (
                <ul className="monitor-list">
                    {monitors.map((monitor) => {
                        const latestCheck = latestChecks[monitor.id]

                        const isChecking =
                            checkingMonitorId === monitor.id

                        const isHistoryOpen =
                            historyMonitorId === monitor.id

                        const monitorCheckError =
                            checkError?.monitorId === monitor.id
                                ? checkError.message
                                : null

                        const isDeleting =
                            deletingMonitorId === monitor.id

                        const monitorDeleteError =
                            deleteError?.monitorId === monitor.id
                                ? deleteError.message
                                : null

                        const isUpdating =
                            updatingMonitorId === monitor.id

                        const monitorUpdateError =
                            updateError?.monitorId === monitor.id
                                ? updateError.message
                                : null

                        return (
                            <li
                                className="monitor-card"
                                key={monitor.id}
                            >
                                <div className="monitor-card-header">
                                    <div>
                                        <span
                                            className={
                                                monitor.enabled
                                                    ? "status-badge enabled"
                                                    : "status-badge disabled"
                                            }
                                        >
                                            <span className="status-dot" />

                                            {monitor.enabled
                                                ? "Enabled"
                                                : "Paused"}
                                        </span>

                                        <h3>{monitor.name}</h3>
                                    </div>

                                    <span className="monitor-id">
                                        #{monitor.id}
                                    </span>
                                </div>

                                <a
                                    className="monitor-url"
                                    href={monitor.url}
                                    target="_blank"
                                    rel="noreferrer"
                                >
                                    {monitor.url}
                                </a>

                                <dl className="monitor-meta">
                                    <div>
                                        <dt>Expected</dt>
                                        <dd>
                                            {monitor.expected_status_code}
                                        </dd>
                                    </div>

                                    <div>
                                        <dt>Interval</dt>
                                        <dd>{monitor.interval_seconds}s</dd>
                                    </div>

                                    <div>
                                        <dt>Timeout</dt>
                                        <dd>{monitor.timeout_seconds}s</dd>
                                    </div>
                                </dl>

                                <div className="monitor-actions">
                                    <button
                                        className="secondary-button"
                                        type="button"
                                        disabled={checkingMonitorId !== null}
                                        onClick={() => {
                                            void onCheck(monitor.id)
                                        }}
                                    >
                                        <PulseIcon />
                                        {isChecking
                                            ? "Checking..."
                                            : "Check now"}
                                    </button>

                                    <button
                                        className="secondary-button"
                                        type="button"
                                        onClick={() => {
                                            setHistoryMonitorId((current) =>
                                                current === monitor.id
                                                    ? null
                                                    : monitor.id,
                                            )
                                        }}
                                    >
                                        <ClockIcon />
                                        {isHistoryOpen
                                            ? "Hide history"
                                            : "History"}
                                    </button>

                                    <button
                                        className={`toggle-button ${
                                            monitor.enabled ? "pause" : "enable"
                                        }`}
                                        type="button"
                                        disabled={
                                            checkingMonitorId !== null ||
                                            deletingMonitorId !== null ||
                                            updatingMonitorId !== null
                                        }
                                        onClick={() => {
                                            void onToggleEnabled(monitor)
                                        }}
                                    >
                                        <ToggleIcon enabled={monitor.enabled} />
                                        {isUpdating
                                            ? "Updating..."
                                            : monitor.enabled
                                              ? "Pause"
                                              : "Enable"}
                                    </button>

                                    <button
                                        className="danger-button"
                                        type="button"
                                        disabled={
                                            deletingMonitorId !== null ||
                                            checkingMonitorId !== null ||
                                            updatingMonitorId !== null
                                        }
                                        onClick={() => {
                                            void onDelete(monitor)
                                        }}
                                    >
                                        <TrashIcon />
                                        {isDeleting
                                            ? "Deleting..."
                                            : "Delete"}
                                    </button>
                                </div>

                                {latestCheck && (
                                    <div
                                        className={`check-result ${latestCheck.status}`}
                                    >
                                        <div className="check-result-header">
                                            <strong>
                                                {latestCheck.status.toUpperCase()}
                                            </strong>

                                            <span>
                                                {new Date(
                                                    latestCheck.checked_at,
                                                ).toLocaleString()}
                                            </span>
                                        </div>

                                        <div className="check-result-details">
                                            <span>
                                                HTTP{" "}
                                                {latestCheck.status_code ?? "—"}
                                            </span>

                                            <span>
                                                {latestCheck.latency_ms} ms
                                            </span>
                                        </div>

                                        {latestCheck.error && (
                                            <p>{latestCheck.error}</p>
                                        )}
                                    </div>
                                )}

                                {monitorCheckError && (
                                    <p
                                        className="alert check-error"
                                        role="alert"
                                    >
                                        {monitorCheckError}
                                    </p>
                                )}

                                {monitorDeleteError && (
                                    <p
                                        className="alert check-error"
                                        role="alert"
                                    >
                                        {monitorDeleteError}
                                    </p>
                                )}

                                {monitorUpdateError && (
                                    <p
                                        className="alert check-error"
                                        role="alert"
                                    >
                                        {monitorUpdateError}
                                    </p>
                                )}

                                {isHistoryOpen && (
                                    <CheckHistory
                                        monitorId={monitor.id}
                                        refreshKey={latestCheck?.id}
                                    />
                                )}
                            </li>
                        )
                    })}
                </ul>
            )}
        </section>
    )
}
