/**
 * Shared browser-side rules for static replay evidence. This module deliberately
 * contains no React code so its request lifecycle and display gates can be
 * exercised with the same implementation used by the explorer.
 */

export function replayState(selectedRunId, replay, error) {
  if (!selectedRunId) return "aggregate";
  if (error) return "unavailable";
  return replay?.run?.run_id === selectedRunId ? "verified" : "pending";
}

export function eventGeometry(days, width = 640) {
  if (!days.length) return { min: null, max: null, points: [] };

  const eventDays = days.map((day) => day.event_day);
  const min = Math.min(...eventDays);
  const max = Math.max(...eventDays);

  return {
    min,
    max,
    points: days.map((day) => ({
      ...day,
      x: eventDayPosition({ min, max }, day.event_day, width),
    })),
  };
}

export function eventDayPosition({ min, max }, eventDay, width = 640) {
  if (min === null || max === null) return null;
  const span = max - min || 1;
  return ((eventDay - min) / span) * width;
}

export function eventDayTicks({ min, max }) {
  if (min === null || max === null) return [];
  if (min === max) return [min];
  const middle = Math.round((min + max) / 2);
  return [...new Set([min, middle, max])];
}

export function replayMetrics(state, replay, evaluationComplaints) {
  const withheld = state === "unavailable" ? "Unavailable" : "Replay pending";

  if (state !== "verified" || !replay) {
    return {
      found: withheld,
      unfound: withheld,
      service: withheld,
      delay: withheld,
      deferrals: withheld,
    };
  }

  const { run, daily_event_series: days } = replay;
  const attempts = days.reduce((total, day) => total + day.inspection_attempts, 0);
  const deferrals = days.reduce((total, day) => total + day.deferred, 0);

  return {
    found: `${run.actionable_found} / ${run.latent_actionable_total}`,
    unfound: `${run.actionable_unfound} / ${run.latent_actionable_total}`,
    service: evaluationComplaints
      ? `${((attempts / evaluationComplaints) * 100).toFixed(0)}%`
      : "Not comparable",
    delay:
      run.mean_delay_days === null
        ? "Not comparable"
        : `${run.mean_delay_days.toFixed(1)} days`,
    deferrals: `${deferrals} explicit deferrals in this seed`,
  };
}

export class ReplayLoader {
  identity = 0;

  invalidate() {
    this.identity += 1;
    return this.identity;
  }

  async load(selectedRunId, entry, fetchText, parse, verifyText, isAborted = () => false) {
    const token = this.invalidate();
    const stale = () => token !== this.identity || isAborted();
    const ignored = () => ({ stale: true, value: null, error: null });

    if (!entry) {
      return {
        stale: false,
        value: null,
        error: "Replay index entry unavailable. Event-day evidence is withheld.",
      };
    }

    try {
      const text = await fetchText();
      if (stale()) return ignored();

      const verified = await verifyText(text, entry.sha256);
      if (stale()) return ignored();
      if (!verified) {
        return {
          stale: false,
          value: null,
          error: "Replay integrity verification failed. Event-day evidence is withheld.",
        };
      }

      const value = await parse(text);
      if (stale()) return ignored();
      if (value?.run?.run_id !== selectedRunId) {
        return {
          stale: false,
          value: null,
          error: "Replay identity mismatch. Event-day evidence is withheld.",
        };
      }

      return { stale: false, value, error: null };
    } catch {
      if (stale()) return ignored();
      return {
        stale: false,
        value: null,
        error: "Replay unavailable. Event-day evidence is withheld.",
      };
    }
  }
}
