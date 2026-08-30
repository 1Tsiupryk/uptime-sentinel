import { useState, type SubmitEvent } from "react"

import { createMonitor } from "../api/client"
import type { Monitor, MonitorCreate } from "../types/monitor"

interface MonitorFormProps {
    onCreated: (monitor: Monitor) => void
}

const initialForm: MonitorCreate = {
    name: "",
    url: "",
    interval_seconds: 60,
    timeout_seconds: 5,
    expected_status_code: 200,
    enabled: true,
}

export function MonitorForm({ onCreated }: MonitorFormProps) {
    const [form, setForm] = useState<MonitorCreate>(initialForm)
    const [isSubmitting, setIsSubmitting] = useState(false)
    const [error, setError] = useState<string | null>(null)

    async function handleSubmit(
        event: SubmitEvent<HTMLFormElement>,
    ) {
        event.preventDefault()

        try {
            setIsSubmitting(true)
            setError(null)

            const createdMonitor = await createMonitor(form)

            onCreated(createdMonitor)
            setForm(initialForm)
        } catch (error) {
            setError(
                error instanceof Error
                    ? error.message
                    : "Failed to create monitor",
            )
        } finally {
            setIsSubmitting(false)
        }
    }

    return (
        <section className="panel form-panel">
            <header className="section-heading">
                <span className="eyebrow">Configuration</span>
                <h2>Add monitor</h2>
                <p>Create a new endpoint health check.</p>
            </header>

            <form className="monitor-form" onSubmit={handleSubmit}>
                <label className="field field-wide">
                    <span>Name</span>

                    <input
                        type="text"
                        required
                        maxLength={200}
                        placeholder="Production API"
                        value={form.name}
                        onChange={(event) =>
                            setForm((current) => ({
                                ...current,
                                name: event.target.value,
                            }))
                        }
                    />
                </label>

                <label className="field field-wide">
                    <span>URL</span>

                    <input
                        type="url"
                        required
                        placeholder="https://example.com"
                        value={form.url}
                        onChange={(event) =>
                            setForm((current) => ({
                                ...current,
                                url: event.target.value,
                            }))
                        }
                    />
                </label>

                <label className="field">
                    <span>Expected status</span>

                    <input
                        type="number"
                        required
                        min={100}
                        max={599}
                        value={form.expected_status_code}
                        onChange={(event) =>
                            setForm((current) => ({
                                ...current,
                                expected_status_code: Number(event.target.value),
                            }))
                        }
                    />
                </label>

                <label className="field">
                    <span>Interval, seconds</span>

                    <input
                        type="number"
                        required
                        min={10}
                        max={86400}
                        value={form.interval_seconds}
                        onChange={(event) =>
                            setForm((current) => ({
                                ...current,
                                interval_seconds: Number(event.target.value),
                            }))
                        }
                    />
                </label>

                <label className="field field-wide">
                    <span>Timeout, seconds</span>

                    <input
                        type="number"
                        required
                        min={1}
                        max={60}
                        value={form.timeout_seconds}
                        onChange={(event) =>
                            setForm((current) => ({
                                ...current,
                                timeout_seconds: Number(event.target.value),
                            }))
                        }
                    />
                </label>

                <label className="checkbox-field field-wide">
                    <input
                        type="checkbox"
                        checked={form.enabled}
                        onChange={(event) =>
                            setForm((current) => ({
                                ...current,
                                enabled: event.target.checked,
                            }))
                        }
                    />

                    <span>Enable scheduled checks</span>
                </label>

                <button
                    className="primary-button field-wide"
                    type="submit"
                    disabled={isSubmitting}
                >
                    {isSubmitting ? "Creating..." : "Create monitor"}
                </button>

                {error && (
                    <p className="alert field-wide" role="alert">
                        {error}
                    </p>
                )}
            </form>
        </section>
    )
}