export interface Monitor {
    id: number
    name: string
    url: string
    interval_seconds: number
    timeout_seconds: number
    expected_status_code: number
    enabled: boolean
    created_at: string
}

export interface MonitorCreate {
    name: string
    url: string
    interval_seconds: number
    timeout_seconds: number
    expected_status_code: number
    enabled: boolean
}

export type MonitorUpdate = Partial<MonitorCreate>

export interface CheckResult {
    id: number
    monitor_id: number
    status: "up" | "down"
    status_code: number | null
    latency_ms: number
    error: string | null
    checked_at: string
}