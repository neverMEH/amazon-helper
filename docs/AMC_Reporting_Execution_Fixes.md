## AMC Reporting Execution: Fixes and Implementation Guide

Audience: An LLM or developer applying concrete edits to align our execution flow with Amazon Marketing Cloud (AMC) Reporting API.

Primary docs: [AMC Reporting API](https://advertising.amazon.com/API/docs/en-us/amc-reporting)

### Goals
- Ensure executions are always created against saved AMC workflows (`workflowId`).
- Remove ad‑hoc execution payloads not in AMC Reporting API.
- Make execution time window and time zone configurable per run.
- Avoid blocking sleeps in HTTP request paths; use non‑blocking polling.
- Persist AMC output metadata (`outputLocation`, `rowCount`, `sizeBytes`) with execution records.
- Validate and restrict `outputFormat` to supported values.

---

### Quick Summary of Changes
1) Remove ad‑hoc execution fallback; require `workflowId`.
2) Parameterize time window/time zone via `execution_parameters`.
3) Replace blocking `time.sleep(...)` in status polling endpoint with immediate return logic.
4) Persist `outputLocation`, `rowCount`, `dataSizeBytes` on completion.
5) Validate `output_format` input.

---

### Files and Functions to Edit

1) `amc_manager/services/amc_execution_service.py`
   - Function: `_execute_real_amc_query(...)`
   - Function: `poll_and_update_execution(...)`
   - Function: `_update_execution_completed(...)`

2) `amc_manager/services/amc_api_client.py`
   - Function: `create_workflow_execution(...)`
   - Function: `get_execution_status(...)`
   - Function: `get_execution_results(...)`

3) (Optional UX) `frontend/src/components/workflows/ExecutionModal.tsx`
   - Pass time window/time zone and `output_format` parameters when executing.

---

### Detailed Edit Plan (Step‑by‑Step)

#### 1) Enforce saved workflow execution only
- Location: `amc_manager/services/amc_api_client.py::create_workflow_execution`
- Action:
  - Remove/disable the ad‑hoc branch that posts a `workflow` object with embedded SQL.
  - Require `workflow_id` to be provided. If missing, return an error.
- Also update call site:
  - Location: `amc_manager/services/amc_execution_service.py::_execute_real_amc_query`
  - Remove the ad‑hoc fallback path. If `amc_workflow_id` is absent, return a failure or ensure the auto‑creation step runs before calling here.

Acceptance:
- When executing, we always send body containing `{ "workflowId": "...", ... }` to `/amc/reporting/{instanceId}/workflowExecutions`.

#### 2) Parameterize time window and time zone
- Locations:
  - `amc_manager/services/amc_api_client.py::create_workflow_execution`
  - `amc_manager/services/amc_execution_service.py::_execute_real_amc_query`
- Action:
  - Accept optional keys from `execution_parameters`:
    - `timeWindowType` (default: `EXPLICIT`)
    - `timeWindowStart` (ISO `YYYY-MM-DDTHH:mm:ss`)
    - `timeWindowEnd` (ISO `YYYY-MM-DDTHH:mm:ss`)
    - `timeWindowTimeZone` (default: `UTC`)
    - `output_format` (default: `CSV`)
  - Build the payload using these values when present; otherwise use sensible defaults (e.g., last 7 days window, tz `UTC`).

Example payload body fields to send to AMC on create execution:
```json
{
  "workflowId": "my_workflow_123",
  "timeWindowType": "EXPLICIT",
  "timeWindowStart": "2025-08-08T00:00:00",
  "timeWindowEnd": "2025-08-11T23:59:59",
  "timeWindowTimeZone": "UTC",
  "outputFormat": "CSV",
  "parameterValues": { /* user-provided named parameters */ }
}
```

Acceptance:
- If the frontend sends time window params, they appear in AMC request body. Otherwise defaults (configurable) are applied.

#### 3) Remove blocking sleep in polling endpoint
- Location: `amc_manager/services/amc_execution_service.py::poll_and_update_execution`
- Current anti‑pattern:
  - A `time.sleep(45)` happens on the first status check when status is `pending`.
- Action:
  - Remove the blocking `sleep`. Instead, immediately query AMC once and return current status to the frontend.
  - Keep simple retry (short, non‑blocking) if desired, but avoid long sleeps in request path. Frontend/clients will keep polling.

Acceptance:
- The `/workflows/executions/{execution_id}/status` endpoint returns within typical HTTP latency with current status, no long server‑side waits.

#### 4) Persist output metadata on completion
- Locations:
  - `amc_manager/services/amc_execution_service.py::poll_and_update_execution` (collect values)
  - `amc_manager/services/amc_execution_service.py::_update_execution_completed` (store values)
- Action:
  - After a successful status check, capture:
    - From `get_execution_status`: `outputLocation`
    - From `get_execution_results`: `rowCount`, and from `metadata` use `dataSizeBytes` (if present)
  - Extend `_update_execution_completed(...)` to include:
    - `output_location`, `size_bytes` (if schema supports), `row_count` (already handled)
  - Ensure the DB columns exist (see `database/supabase/07_execution_results_fields.sql`). If missing, add a migration or gate fields with presence check.

Acceptance:
- `/workflows/executions/{execution_id}/detail` returns `output_location` and `size_bytes` populated for completed runs that have them.

#### 5) Validate `output_format`
- Location: `amc_manager/services/amc_execution_service.py::_execute_real_amc_query`
- Action:
  - Accept only `CSV` or `PARQUET`. Default to `CSV` if absent.
  - Reject others with a clear error message before calling AMC.

Acceptance:
- Invalid `output_format` values are rejected with a 400 error, and AMC is not called.

---

### API Contracts to Honor
- Create execution: `POST /amc/reporting/{instanceId}/workflowExecutions`
  - Body must include `workflowId` and time window fields as supported by AMC Reporting.
  - Required headers: `Amazon-Advertising-API-ClientId`, `Authorization`, `Amazon-Advertising-API-AdvertiserId`, `Amazon-Advertising-API-MarketplaceId`.
- Status: `GET /amc/reporting/{instanceId}/workflowExecutions/{executionId}`
  - Map AMC statuses: `PENDING`→`pending`, `RUNNING`→`running`, `SUCCEEDED`→`completed`, `FAILED|CANCELLED`→`failed`.
- Download URLs: `GET /amc/reporting/{instanceId}/workflowExecutions/{executionId}/downloadUrls`
  - Parse first CSV URL, download, parse, and store columns/rows/metadata.

Reference: [AMC Reporting API](https://advertising.amazon.com/API/docs/en-us/amc-reporting)

---

### Concrete Edit Snippets (what to change)

- In `amc_manager/services/amc_api_client.py::create_workflow_execution`:
  - Delete the branch that sets `payload = { "workflow": { ... "sql": sql_query ... } }`.
  - Add extraction of time window fields from function args (or kwargs) passed down from `amc_execution_service`.
  - If `workflow_id` is falsy: return `{ "success": False, "error": "workflowId is required" }`.

- In `amc_manager/services/amc_execution_service.py::_execute_real_amc_query`:
  - Remove the `else` fallback that calls `create_workflow_execution` with `sql_query`.
  - Build `payload` options for time window/time zone/output format from `execution_parameters`.
  - Validate `output_format in {"CSV","PARQUET"}`.

- In `amc_manager/services/amc_execution_service.py::poll_and_update_execution`:
  - Remove `time.sleep(45)`; keep logic to query status once per HTTP call.
  - On success path, capture `outputLocation` from status and `rowCount`/`metadata.dataSizeBytes` from results; pass to `_update_execution_completed`.

- In `amc_manager/services/amc_execution_service.py::_update_execution_completed`:
  - Include optional fields in `update_data`: `output_location`, `size_bytes` (if provided).

---

### Test Plan
- Unit/Integration (manual OK):
  - Start a workflow execution where `amc_workflow_id` exists; ensure request to AMC contains `workflowId` and time window.
  - Attempt execution without `workflowId` (simulate by skipping sync): verify we fail early (no ad‑hoc post).
  - Poll status endpoint repeatedly; verify no long server response times and that status transitions occur.
  - Upon completion, verify DB row has `output_location`, `row_count`, and `size_bytes` (if returned) and that `/detail` returns them.
  - Try `output_format=PARQUET` and invalid value (e.g., `JSON`) to validate enforcement.

Frontend checks:
  - `ExecutionModal` can pass time window/time zone and `output_format` in request body.
  - Status polling frequency remains as configured; responses are quick.

---

### Rollback Plan
- If issues arise, re‑enable the prior `time.sleep(...)` temporarily and revert to previous create‑execution branch. Avoid keeping both code paths long‑term.

---

### Acceptance Criteria (Checklist)
- [ ] No ad‑hoc SQL payloads sent to AMC; executions require `workflowId`.
- [ ] Time window/time zone are configurable per execution and appear in AMC request body.
- [ ] Status endpoint returns quickly; no blocking sleeps remain.
- [ ] Completed executions persist `output_location`, `row_count`, and `size_bytes` (when available) and surface them via `/detail`.
- [ ] `output_format` validated to supported values.


