"use client";

import { useMemo, useState } from "react";

const gatewayBase = process.env.NEXT_PUBLIC_GATEWAY_URL || "http://localhost:8080";

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [type, setType] = useState("tourism");
  const [apiKey, setApiKey] = useState("");
  const [jobId, setJobId] = useState("");
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const headers = useMemo(() => {
    const h = { "Content-Type": "application/json" };
    if (apiKey.trim()) {
      h["X-API-Key"] = apiKey.trim();
    }
    return h;
  }, [apiKey]);

  async function startExtraction(e) {
    e.preventDefault();
    setError("");
    setStatus(null);
    setJobId("");
    setLoading(true);

    try {
      const res = await fetch(`${gatewayBase}/api/v1/extract`, {
        method: "POST",
        headers,
        body: JSON.stringify({ url, type })
      });

      const body = await res.json();
      if (!res.ok) {
        throw new Error(body.error || "Failed to start extraction");
      }

      setJobId(body.job_id);
      await pollStatus(body.job_id, headers);
    } catch (err) {
      setError(err.message || "Unexpected error");
    } finally {
      setLoading(false);
    }
  }

  async function pollStatus(id, currentHeaders) {
    for (let i = 0; i < 120; i += 1) {
      const res = await fetch(`${gatewayBase}/api/v1/status/${id}`, {
        method: "GET",
        headers: currentHeaders
      });

      const body = await res.json();
      if (!res.ok) {
        setStatus({ stage: "error", message: body.error || "status request failed" });
        return;
      }

      setStatus(body);
      if (body.stage === "done" || body.stage === "error") {
        return;
      }

      await new Promise((r) => setTimeout(r, 2000));
    }

    setStatus({ stage: "timeout", message: "Status polling timed out after 4 minutes." });
  }

  return (
    <main style={{ maxWidth: 900, margin: "40px auto", padding: 24 }}>
      <h1 style={{ marginBottom: 8 }}>Momentos Control Panel</h1>
      <p style={{ marginTop: 0, color: "#465267" }}>
        Trigger extraction jobs and monitor pipeline progress from your server.
      </p>

      <form onSubmit={startExtraction} style={{ background: "#fff", borderRadius: 12, padding: 20, boxShadow: "0 10px 30px rgba(0,0,0,0.06)" }}>
        <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Source URL</label>
        <input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://example.com/article"
          required
          style={{ width: "100%", padding: "12px 14px", marginBottom: 14, borderRadius: 8, border: "1px solid #c8d2e1" }}
        />

        <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>Content Type</label>
        <select
          value={type}
          onChange={(e) => setType(e.target.value)}
          style={{ width: "100%", padding: "12px 14px", marginBottom: 14, borderRadius: 8, border: "1px solid #c8d2e1" }}
        >
          <option value="tourism">tourism</option>
          <option value="course">course</option>
        </select>

        <label style={{ display: "block", marginBottom: 8, fontWeight: 600 }}>API Key (optional)</label>
        <input
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="X-API-Key value if enabled"
          style={{ width: "100%", padding: "12px 14px", marginBottom: 18, borderRadius: 8, border: "1px solid #c8d2e1" }}
        />

        <button
          type="submit"
          disabled={loading}
          style={{
            background: loading ? "#7f8ba3" : "#1f4dd8",
            color: "#fff",
            border: "none",
            borderRadius: 8,
            padding: "10px 14px",
            fontWeight: 600,
            cursor: loading ? "not-allowed" : "pointer"
          }}
        >
          {loading ? "Processing..." : "Start Job"}
        </button>
      </form>

      {error ? (
        <div style={{ marginTop: 18, background: "#ffe5e5", color: "#9f1d1d", border: "1px solid #ffb8b8", borderRadius: 10, padding: 12 }}>
          {error}
        </div>
      ) : null}

      {jobId ? (
        <div style={{ marginTop: 16, color: "#1f2a3c" }}>
          <strong>Job ID:</strong> {jobId}
        </div>
      ) : null}

      {status ? (
        <section style={{ marginTop: 18, background: "#fff", borderRadius: 12, padding: 18, boxShadow: "0 8px 24px rgba(0,0,0,0.05)" }}>
          <h2 style={{ marginTop: 0, marginBottom: 10 }}>Latest Status</h2>
          <p style={{ margin: "6px 0" }}><strong>Stage:</strong> {status.stage || "unknown"}</p>
          <p style={{ margin: "6px 0" }}><strong>Message:</strong> {status.message || "-"}</p>
          <p style={{ margin: "6px 0" }}><strong>Progress:</strong> {typeof status.progress === "number" ? `${Math.round(status.progress * 100)}%` : "-"}</p>
        </section>
      ) : null}
    </main>
  );
}
