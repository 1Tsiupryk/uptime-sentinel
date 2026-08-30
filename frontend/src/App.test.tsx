import { render, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, test, vi } from "vitest"

import App from "./App"
import {
  createMonitor,
  getMonitors,
  triggerCheck,
} from "./api/client"
import type { CheckResult, Monitor } from "./types/monitor"

vi.mock("./api/client", () => ({
  createMonitor: vi.fn(),
  deleteMonitor: vi.fn(),
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

describe("Uptime Sentinel dashboard", () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(getMonitors).mockResolvedValue([])
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
})
