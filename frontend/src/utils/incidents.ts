import type { Incident } from "../types/incident"


export const INCIDENT_POLL_INTERVAL_MS = 10_000

export function getIncidentDurationMs(
  incident: Incident,
  now = Date.now(),
): number {
  const startedAt = new Date(incident.started_at).getTime()
  const endedAt = incident.resolved_at
    ? new Date(incident.resolved_at).getTime()
    : now

  return Math.max(0, endedAt - startedAt)
}

export function formatDuration(durationMs: number): string {
  const totalSeconds = Math.floor(durationMs / 1000)

  if (totalSeconds < 60) {
    return `${totalSeconds}s`
  }

  const totalMinutes = Math.floor(totalSeconds / 60)

  if (totalMinutes < 60) {
    return `${totalMinutes}m ${totalSeconds % 60}s`
  }

  const totalHours = Math.floor(totalMinutes / 60)

  if (totalHours < 24) {
    return `${totalHours}h ${totalMinutes % 60}m`
  }

  const totalDays = Math.floor(totalHours / 24)
  return `${totalDays}d ${totalHours % 24}h`
}

export function formatIncidentDuration(incident: Incident): string {
  return formatDuration(getIncidentDurationMs(incident))
}
