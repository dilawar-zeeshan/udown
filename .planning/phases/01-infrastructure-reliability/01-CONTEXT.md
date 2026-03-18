# Phase 1: Infrastructure reliability - Context

**Gathered:** 2026-03-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Robust metadata extraction via background yt-dlp workers and frontend display.

</domain>

<decisions>
## Implementation Decisions

### Error Presentation
- **Error Details:** Generic, user-friendly message (do not expose raw yt-dlp errors to end users).
- **Recovery Action:** Provide a dedicated "Retry" button.
- **Visual Style:** Show the error inline below the input box (least disruptive).
- **Validation:** Perform local regex validation on the URL before queueing the job to the worker.

### Claude's Discretion
- Loading States indicator and worker timeout logic are left to Claude's discretion.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

No external specs — requirements fully captured in decisions above.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `frontend/src/api.js`: Contains `getVideoInfo` function and uses a Supabase polling loop `pollJob`.
- `frontend/src/App.jsx`: Exists and has a `STATUS_CONFIG` mechanism that could be adapted for inline errors.

### Established Patterns
- Asynchronous Supabase table polling (`downloads_queue`) for worker job delegation.

### Integration Points
- Frontend UI should append the inline error and Retry mechanism around the form in `App.jsx`.

</code_context>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-infrastructure-reliability*
*Context gathered: 2026-03-18*
