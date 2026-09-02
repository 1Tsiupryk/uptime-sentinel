export interface Incident {
  id: number
  monitor_id: number
  started_at: string
  resolved_at: string | null
  opening_check_id: number
  closing_check_id: number | null
}

export type IncidentStatus = "open" | "resolved"
