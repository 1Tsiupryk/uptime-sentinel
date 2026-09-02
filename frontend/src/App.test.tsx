import { act, render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, test, vi } from "vitest"

import App from "./App"
import {
  createMonitor,
  getIncident,
  getIncidents,
  getMonitorIncidents,
  getMonitors,
  triggerCheck,
} from "./api/client"
import type { Incident } from "./types/incident"
import type { CheckResult, Monitor } from "./types/monitor"
import { INCIDENT_POLL_INTERVAL_MS } from "./utils/incidents"

vi.mock("./api/client", () => ({
  createMonitor: vi.fn(),
  deleteMonitor: vi.fn(),
  getIncident: vi.fn(),
  getIncidents: vi.fn(),
  getMonitorIncidents: vi.fn(),
  getMonitorChecks: vi.fn(),
  getMonitors: vi.fn(),
  triggerCheck: vi.fn(),
  updateMonitor: vi.fn(),
}))

const monitor: Monitor = {
  id: 1,
  name: "Production API",
  url: "https://example.com/",
  interval_seconds: 60,
  timeout_seconds: 5,
  expected_status_code: 200,
  enabled: true,
  created_at: "2026-08-27T10:00:00Z",
}

const successfulCheck: CheckResult = {
  id: 10,
  monitor_id: monitor.id,
  status: "up",
  status_code: 200,
  latency_ms: 123,
  error: null,
  checked_at: "2026-08-27T10:01:00Z",
}

const activeIncident: Incident = {
  id: 20,
  monitor_id: monitor.id,
  started_at: "2026-09-02T09:15:00Z",
  resolved_at: null,
  opening_check_id: 58,
  closing_check_id: null,
}

const secondMonitor: Monitor = {
  ...monitor,
  id: 2,
  name: "Internal API",
  url: "https://internal.example.com/",
}

const resolvedIncident: Incident = {
  id: 19,
  monitor_id: secondMonitor.id,
  started_at: "2026-09-01T10:00:00Z",
  resolved_at: "2026-09-01T10:05:00Z",
  opening_check_id: 50,
  closing_check_id: 51,
}

describe("Uptime Sentinel dashboard", () => {
  beforeEach(() => {
    vi.resetAllMocks()
    window.history.pushState({}, "", "/")
    vi.mocked(getMonitors).mockResolvedValue([])
    vi.mocked(getIncidents).mockResolvedValue([])
    vi.mocked(getMonitorIncidents).mockResolvedValue([])
    vi.mocked(getIncident).mockResolvedValue(activeIncident)
  })

  test("loads and displays monitors", async () => {
    vi.mocked(getMonitors).mockResolvedValue([monitor])

    render(<App />)

    expect(
      await screen.findByRole("heading", {
        name: "Production API",
      }),
    ).toBeInTheDocument()

    expect(
      screen.getByRole("link", {
        name: "https://example.com/",
      }),
    ).toHaveAttribute("href", "https://example.com/")
  })

  test("creates a monitor and adds it to the list", async () => {
    const user = userEvent.setup()
    vi.mocked(createMonitor).mockResolvedValue(monitor)

    render(<App />)

    await user.type(
      screen.getByRole("textbox", { name: "Name" }),
      "Production API",
    )
    await user.type(
      screen.getByRole("textbox", { name: "URL" }),
      "https://example.com",
    )
    await user.click(
      screen.getByRole("button", { name: "Create monitor" }),
    )

    await waitFor(() => {
      expect(createMonitor).toHaveBeenCalledWith({
        name: "Production API",
        url: "https://example.com",
        interval_seconds: 60,
        timeout_seconds: 5,
        expected_status_code: 200,
        enabled: true,
      })
    })

    expect(
      await screen.findByRole("heading", {
        name: "Production API",
      }),
    ).toBeInTheDocument()
  })

  test("runs a check and displays its result", async () => {
    const user = userEvent.setup()
    vi.mocked(getMonitors).mockResolvedValue([monitor])
    vi.mocked(triggerCheck).mockResolvedValue(successfulCheck)

    render(<App />)

    await user.click(
      await screen.findByRole("button", {
        name: "Check now",
      }),
    )

    expect(await screen.findByText("UP")).toBeInTheDocument()
    expect(screen.getByText("HTTP 200")).toBeInTheDocument()
    expect(screen.getByText("123 ms")).toBeInTheDocument()
    expect(triggerCheck).toHaveBeenCalledWith(monitor.id)
  })

  test("marks a monitor with an active incident", async () => {
    vi.mocked(getMonitors).mockResolvedValue([monitor])
    vi.mocked(getIncidents).mockResolvedValue([activeIncident])

    render(<App />)

    expect(
      await screen.findByText(/Active incident/),
    ).toBeInTheDocument()
    expect(
      screen.getByRole("link", { name: "1 active incident" }),
    ).toBeInTheDocument()
    expect(screen.getByText("monitor")).toBeInTheDocument()
  })

  test("polls active incidents in the background", async () => {
    const setIntervalSpy = vi.spyOn(window, "setInterval")
    vi.mocked(getIncidents)
      .mockResolvedValueOnce([])
      .mockResolvedValue([activeIncident])

    render(<App />)

    await waitFor(() => {
      expect(getIncidents).toHaveBeenCalledWith("open")
    })

    const pollingCall = setIntervalSpy.mock.calls.find(
      ([, delay]) => delay === INCIDENT_POLL_INTERVAL_MS,
    )

    expect(pollingCall).toBeDefined()
    const pollingCallback = pollingCall?.[0]

    if (typeof pollingCallback !== "function") {
      throw new Error("Incident polling callback was not registered")
    }

    act(() => {
      pollingCallback()
    })

    expect(
      await screen.findByRole("link", { name: "1 active incident" }),
    ).toBeInTheDocument()

    setIntervalSpy.mockRestore()
  })

  test("opens the incidents page and filters resolved incidents", async () => {
    const user = userEvent.setup()
    vi.mocked(getMonitors).mockResolvedValue([monitor, secondMonitor])
    vi.mocked(getIncidents).mockImplementation((status) =>
      Promise.resolve(
        status === "open"
          ? [activeIncident]
          : [activeIncident, resolvedIncident],
      ),
    )

    render(<App />)

    await user.click(
      screen.getByRole("link", { name: "Incidents" }),
    )

    expect(
      await screen.findByRole("heading", { name: "Incidents" }),
    ).toBeInTheDocument()
    expect(await screen.findByText("Production API")).toBeInTheDocument()
    expect(screen.getByText("Internal API")).toBeInTheDocument()

    await user.click(
      screen.getByRole("button", {
        name: "Sort incidents: Newest first",
      }),
    )
    await user.click(
      screen.getByRole("option", { name: "Shortest duration" }),
    )

    expect(
      screen.getByRole("button", {
        name: "Sort incidents: Shortest duration",
      }),
    ).toBeInTheDocument()

    await user.click(
      screen.getByRole("button", { name: "Resolved" }),
    )

    expect(screen.queryByText("Production API")).not.toBeInTheDocument()
    expect(screen.getByText("Internal API")).toBeInTheDocument()
  })
})
