import type {
    CheckResult,
    Monitor,
    MonitorCreate,
    MonitorUpdate,
} from "../types/monitor"
import type { Incident, IncidentStatus } from "../types/incident"

const API_URL =
    import.meta.env.VITE_API_URL ?? "http://localhost:8000"

async function request<T>(
    path: string,
    options?: RequestInit,
): Promise<T> {
    const headers = new Headers(options?.headers)

    if (options?.body !== undefined) {
        headers.set("Content-Type", "application/json")
    }

    const response = await fetch(`${API_URL}${path}`, {
        ...options,
        headers,
    })

    if (!response.ok) {
        const body = await response.text()

        throw new Error(
            body || `API request failed with status ${response.status}`,
        )
    }

    return response.json() as Promise<T>
}

export function getMonitors(): Promise<Monitor[]> {
    return request<Monitor[]>("/monitors")
}

export function createMonitor(
    monitor: MonitorCreate,
): Promise<Monitor> {
    return request<Monitor>("/monitors", {
        method: "POST",
        body: JSON.stringify(monitor),
    })
}

export function updateMonitor(
    monitorId: number,
    update: MonitorUpdate,
): Promise<Monitor> {
    return request<Monitor>(`/monitors/${monitorId}`, {
        method: "PATCH",
        body: JSON.stringify(update),
    })
}

export async function deleteMonitor(
    monitorId: number,
): Promise<void> {
    const response = await fetch(`${API_URL}/monitors/${monitorId}`, {
        method: "DELETE",
    })

    if (!response.ok) {
        throw new Error(
            `Failed to delete monitor: ${response.status}`,
        )
    }
}

export function triggerCheck(
    monitorId: number,
): Promise<CheckResult> {
    return request<CheckResult>(`/monitors/${monitorId}/check`, {
        method: "POST",
    })
}

export function getMonitorChecks(
    monitorId: number,
): Promise<CheckResult[]> {
    return request<CheckResult[]>(
        `/monitors/${monitorId}/checks`,
    )
}

export function getIncidents(
    status?: IncidentStatus,
): Promise<Incident[]> {
    const query = status
        ? `?${new URLSearchParams({ status }).toString()}`
        : ""

    return request<Incident[]>(`/incidents${query}`)
}

export function getIncident(
    incidentId: number,
): Promise<Incident> {
    return request<Incident>(`/incidents/${incidentId}`)
}

export function getMonitorIncidents(
    monitorId: number,
): Promise<Incident[]> {
    return request<Incident[]>(
        `/monitors/${monitorId}/incidents`,
    )
}
