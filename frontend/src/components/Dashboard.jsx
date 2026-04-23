import { useState, useEffect } from "react";
import { listSubmissions, listExams } from "../api/client";

export default function Dashboard() {
  const [submissions, setSubmissions] = useState([]);
  const [exams, setExams] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([listSubmissions(), listExams()])
      .then(([subRes, examRes]) => {
        setSubmissions(subRes.data);
        setExams(examRes.data);
      })
      .finally(() => setLoading(false));

    // Real-time polling every 5s
    const interval = setInterval(() => {
      listSubmissions().then((r) => setSubmissions(r.data));
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const flagged = submissions.filter((s) => s.suspicious);
  const clean = submissions.filter((s) => !s.suspicious);
  const flagRate = submissions.length
    ? ((flagged.length / submissions.length) * 100).toFixed(1)
    : 0;

  // Group flag reasons
  const flagCounts = {};
  flagged.forEach((s) =>
    s.flag_reasons.forEach((r) => {
      const key = r.split(" ")[0]; // first word is the code
      flagCounts[key] = (flagCounts[key] || 0) + 1;
    })
  );

  if (loading) return <div className="loading">Loading dashboard…</div>;

  return (
    <div className="dashboard">
      <h1 className="page-title">Proctoring Dashboard</h1>
      <p className="page-sub">Real-time exam monitoring powered by aumne.ai</p>

      {/* KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card">
          <div className="kpi-value">{exams.length}</div>
          <div className="kpi-label">Total Exams</div>
        </div>
        <div className="kpi-card">
          <div className="kpi-value">{submissions.length}</div>
          <div className="kpi-label">Submissions</div>
        </div>
        <div className="kpi-card flagged">
          <div className="kpi-value">{flagged.length}</div>
          <div className="kpi-label">🚨 Flagged</div>
        </div>
        <div className="kpi-card safe">
          <div className="kpi-value">{clean.length}</div>
          <div className="kpi-label">✅ Clean</div>
        </div>
        <div className="kpi-card rate">
          <div className="kpi-value">{flagRate}%</div>
          <div className="kpi-label">Flag Rate</div>
        </div>
      </div>

      {/* Bar chart */}
      {Object.keys(flagCounts).length > 0 && (
        <div className="section">
          <h2 className="section-title">Flag Breakdown</h2>
          <div className="bar-chart">
            {Object.entries(flagCounts).map(([reason, count]) => (
              <div key={reason} className="bar-row">
                <div className="bar-label">{reason.replace(/_/g, " ")}</div>
                <div className="bar-track">
                  <div
                    className="bar-fill"
                    style={{ width: `${(count / flagged.length) * 100}%` }}
                  />
                </div>
                <div className="bar-count">{count}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent flagged submissions */}
      <div className="section">
        <h2 className="section-title">🚨 Suspicious Submissions</h2>
        {flagged.length === 0 ? (
          <p className="empty">No suspicious submissions detected.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>User</th>
                <th>Exam ID</th>
                <th>Flags</th>
                <th>Time</th>
                <th>AI Audit Note</th>
              </tr>
            </thead>
            <tbody>
              {flagged.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.user_name}</td>
                  <td>{s.exam_id}</td>
                  <td>
                    {s.flag_reasons.map((r, i) => (
                      <span key={i} className="badge red">
                        {r.split(" ")[0]}
                      </span>
                    ))}
                  </td>
                  <td>{s.time_taken_seconds ? `${s.time_taken_seconds}s` : "—"}</td>
                  <td className="audit-cell">{s.audit_log || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* All submissions */}
      <div className="section">
        <h2 className="section-title">All Submissions</h2>
        {submissions.length === 0 ? (
          <p className="empty">No submissions yet.</p>
        ) : (
          <table className="table">
            <thead>
              <tr>
                <th>#</th>
                <th>User</th>
                <th>Exam ID</th>
                <th>Status</th>
                <th>Time</th>
              </tr>
            </thead>
            <tbody>
              {submissions.map((s) => (
                <tr key={s.id}>
                  <td>{s.id}</td>
                  <td>{s.user_name}</td>
                  <td>{s.exam_id}</td>
                  <td>
                    <span className={`badge ${s.suspicious ? "red" : "green"}`}>
                      {s.suspicious ? "🚨 Suspicious" : "✅ Clean"}
                    </span>
                  </td>
                  <td>{s.time_taken_seconds ? `${s.time_taken_seconds}s` : "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </div>
  );
}
