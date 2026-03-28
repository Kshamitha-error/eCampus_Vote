import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import API from "../utils/api";
import Layout from "../components/Layout";
import toast from "react-hot-toast";

function Countdown({ endTime }) {
  const [left, setLeft] = useState("");
  const [urgent, setUrgent] = useState(false);
  useEffect(() => {
    const calc = () => {
      const diff = new Date(endTime) - Date.now();
      if (diff <= 0) { setLeft("Ended"); return; }
      const h = Math.floor(diff / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      setUrgent(diff < 300000); // red if < 5 mins
      setLeft(h > 0 ? `${h}h ${m}m ${s}s` : `${m}m ${s}s`);
    };
    calc();
    const t = setInterval(calc, 1000);
    return () => clearInterval(t);
  }, [endTime]);
  return (
    <span style={{ fontWeight: 800, color: urgent ? "#dc2626" : "#d97706", fontFamily: "'Space Grotesk',sans-serif" }}>
      {left}
    </span>
  );
}

const S = {
  card: { background: "#fff", border: "1.5px solid #dbeafe", borderRadius: 16, boxShadow: "0 2px 12px rgba(59,130,246,0.07)" },
};

export default function ElectionDetail() {
  const { id } = useParams();
  const [election, setElection] = useState(null);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    document.title = "Election Details — eCampus Vote";
    API.get(`/elections/${id}`)
      .then((r) => {
        setElection(r.data);
        document.title = `${r.data.title} — eCampus Vote`;
      })
      .catch(() => toast.error("Failed to load election."))
      .finally(() => setLoading(false));
    return () => { document.title = "eCampus Vote"; };
  }, [id]);

  if (loading) {
    return (
      <Layout>
        <div style={{ padding: "28px 24px", maxWidth: 800, margin: "0 auto" }}>
          <div style={{ ...S.card, padding: "24px 26px", marginBottom: 16 }}>
            <div className="skeleton" style={{ height: 22, width: "60%", borderRadius: 8, marginBottom: 12 }} />
            <div className="skeleton" style={{ height: 14, width: "40%", borderRadius: 6, marginBottom: 8 }} />
            <div className="skeleton" style={{ height: 14, width: "80%", borderRadius: 6 }} />
          </div>
          <div style={{ ...S.card, padding: "24px 26px" }}>
            {[1,2,3].map(i => (
              <div key={i} style={{ display:"flex", alignItems:"center", gap:14, marginBottom: i<3 ? 14 : 0 }}>
                <div className="skeleton" style={{ width:52, height:52, borderRadius:12, flexShrink:0 }} />
                <div style={{ flex:1 }}>
                  <div className="skeleton" style={{ height:15, width:"50%", borderRadius:6, marginBottom:8 }} />
                  <div className="skeleton" style={{ height:12, width:"35%", borderRadius:6 }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </Layout>
    );
  }

  if (!election) {
    return (
      <Layout>
        <div style={{ padding: "28px 24px", maxWidth: 800, margin: "0 auto" }}>
          <div style={{ ...S.card, padding: "60px 20px", textAlign: "center" }}>
            <div style={{ fontSize: 48, marginBottom: 12 }}>😕</div>
            <p style={{ color: "#64748b" }}>Election not found.</p>
          </div>
        </div>
      </Layout>
    );
  }

  const badge = {
    ongoing:   { bg: "#dcfce7", color: "#15803d", label: "🟢 Live Now" },
    upcoming:  { bg: "#fef3c7", color: "#92400e", label: "🕐 Upcoming" },
    ended:     { bg: "#f1f5f9", color: "#64748b", label: "✓ Ended" },
    cancelled: { bg: "#fee2e2", color: "#dc2626", label: "✕ Cancelled" },
  };
  const b = badge[election.status] || badge.ended;

  const sortedCandidates = election.status === "ended"
    ? [...(election.candidates || [])].sort((a, b) => (b.vote_count || 0) - (a.vote_count || 0))
    : (election.candidates || []);

  const maxVotes = sortedCandidates.length
    ? Math.max(...sortedCandidates.map(c => c.vote_count || 0), 1)
    : 1;

  return (
    <Layout>
      <div style={{ padding: "28px 24px 48px", maxWidth: 800, margin: "0 auto" }}>
        <button onClick={() => navigate("/elections")}
          style={{ background: "none", border: "none", color: "#2563eb", fontSize: 13, fontWeight: 600, cursor: "pointer", marginBottom: 20 }}>
          ← Back to Elections
        </button>

        {/* Election info */}
        <div style={{ ...S.card, padding: "24px 26px", marginBottom: 20, animation: "fadeUp 0.4s cubic-bezier(.16,1,.3,1)" }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", flexWrap: "wrap", gap: 10, marginBottom: 14 }}>
            <h1 style={{ fontSize: 22, fontWeight: 800, color: "#1e3a8a", margin: 0, fontFamily: "'Space Grotesk',sans-serif", flex: 1 }}>
              {election.title}
            </h1>
            <span style={{ background: b.bg, color: b.color, borderRadius: 99, padding: "5px 14px", fontSize: 12, fontWeight: 700, flexShrink: 0 }}>
              {b.label}
            </span>
          </div>

          {election.description && (
            <p style={{ fontSize: 14, color: "#64748b", lineHeight: 1.7, marginBottom: 16 }}>{election.description}</p>
          )}

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit,minmax(140px,1fr))", gap: 10, marginBottom: 14 }}>
            {[
              { label: "Start", value: new Date(election.start_time).toLocaleString("en-IN") },
              { label: "End",   value: new Date(election.end_time).toLocaleString("en-IN") },
              { label: "Candidates", value: `${election.candidates?.length || 0}` },
            ].map((item) => (
              <div key={item.label} style={{ background: "#f8faff", borderRadius: 10, padding: "10px 14px", border: "1px solid #e8f0fe" }}>
                <div style={{ fontSize: 11, color: "#94a3b8", fontWeight: 600, marginBottom: 4 }}>{item.label}</div>
                <div style={{ fontSize: 13, fontWeight: 700, color: "#1e3a8a" }}>{item.value}</div>
              </div>
            ))}
          </div>

          {election.status === "ongoing" && (
            <div style={{ background: "#fff7ed", borderRadius: 10, padding: "10px 14px", border: "1px solid #fed7aa", display: "flex", alignItems: "center", gap: 8 }}>
              <span style={{ fontSize: 13, color: "#92400e" }}>⏱ Ends in:</span>
              <Countdown endTime={election.end_time} />
            </div>
          )}
        </div>

        {/* Results for ended elections */}
        {election.status === "ended" && sortedCandidates.length > 0 && (
          <div style={{ ...S.card, padding: "22px 24px", marginBottom: 20, animation: "fadeUp 0.45s cubic-bezier(.16,1,.3,1)" }}>
            <h2 style={{ fontSize: 17, fontWeight: 700, color: "#1e3a8a", marginBottom: 16, fontFamily: "'Space Grotesk',sans-serif" }}>
              🏆 Final Results
            </h2>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {sortedCandidates.map((c, i) => (
                <div key={c.id} style={{ background: i === 0 ? "#f0fdf4" : "#f8faff", border: `1.5px solid ${i === 0 ? "#bbf7d0" : "#e8f0fe"}`, borderRadius: 12, padding: "14px 16px" }}>
                  <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                      {i === 0 && <span style={{ fontSize: 20 }}>🏆</span>}
                      {c.photo_url ? (
                        <img src={c.photo_url} alt={c.name} style={{ width: 40, height: 40, borderRadius: 8, objectFit: "cover", border: "2px solid #dbeafe" }} />
                      ) : (
                        <div style={{ width: 40, height: 40, borderRadius: 8, background: "linear-gradient(135deg,#1d4ed8,#3b82f6)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 800, fontSize: 16 }}>
                          {c.name[0]}
                        </div>
                      )}
                      <div>
                        <div style={{ fontWeight: 700, fontSize: 14, color: "#1e3a8a" }}>{c.name}</div>
                        <div style={{ fontSize: 12, color: "#64748b" }}>{c.branch}{c.year && ` • Year ${c.year}`}</div>
                      </div>
                    </div>
                    <div style={{ textAlign: "right" }}>
                      <div style={{ fontWeight: 800, fontSize: 22, color: i === 0 ? "#16a34a" : "#2563eb", fontFamily: "'Space Grotesk',sans-serif" }}>
                        {c.vote_count || 0}
                      </div>
                      <div style={{ fontSize: 11, color: "#94a3b8" }}>votes</div>
                    </div>
                  </div>
                  <div style={{ background: "#dbeafe", borderRadius: 99, height: 6, overflow: "hidden" }}>
                    <div style={{ background: i === 0 ? "linear-gradient(90deg,#16a34a,#22c55e)" : "linear-gradient(90deg,#1d4ed8,#3b82f6)", height: "100%", width: `${((c.vote_count || 0) / maxVotes) * 100}%`, borderRadius: 99, transition: "width 0.8s ease" }} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Candidates */}
        <h2 style={{ fontSize: 17, fontWeight: 700, color: "#1e3a8a", marginBottom: 14, fontFamily: "'Space Grotesk',sans-serif" }}>
          Candidates ({election.candidates?.length || 0})
        </h2>

        {!election.candidates?.length ? (
          <div style={{ ...S.card, padding: "40px 20px", textAlign: "center" }}>
            <p style={{ color: "#94a3b8", fontSize: 14 }}>No candidates added yet.</p>
          </div>
        ) : (
          <div style={{ display: "grid", gap: 12, marginBottom: 24 }}>
            {sortedCandidates.map((c, i) => (
              <div key={c.id} onClick={() => navigate(`/candidates/${c.id}`)}
                style={{ ...S.card, padding: "16px 18px", cursor: "pointer", display: "flex", alignItems: "center", gap: 14, transition: "all 0.25s cubic-bezier(.16,1,.3,1)", animation: `fadeUp ${0.5+i*0.05}s cubic-bezier(.16,1,.3,1)` }}
                onMouseEnter={(e) => { e.currentTarget.style.borderColor="#3b82f6"; e.currentTarget.style.transform="translateY(-2px)"; e.currentTarget.style.boxShadow="0 8px 24px rgba(59,130,246,0.15)"; }}
                onMouseLeave={(e) => { e.currentTarget.style.borderColor="#dbeafe"; e.currentTarget.style.transform="translateY(0)"; e.currentTarget.style.boxShadow="0 2px 12px rgba(59,130,246,0.07)"; }}
              >
                {c.photo_url ? (
                  <img src={c.photo_url} alt={c.name} style={{ width: 52, height: 52, borderRadius: 12, objectFit: "cover", border: "2px solid #dbeafe", flexShrink: 0 }} />
                ) : (
                  <div style={{ width: 52, height: 52, borderRadius: 12, background: "linear-gradient(135deg,#1d4ed8,#3b82f6)", display: "flex", alignItems: "center", justifyContent: "center", color: "#fff", fontWeight: 800, fontSize: 20, flexShrink: 0 }}>
                    {c.name[0]}
                  </div>
                )}
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 700, fontSize: 15, color: "#1e3a8a", marginBottom: 3 }}>{c.name}</div>
                  <div style={{ fontSize: 12, color: "#64748b" }}>{c.branch}{c.year && ` • Year ${c.year}`}</div>
                </div>
                <span style={{ color: "#94a3b8", fontSize: 20 }}>›</span>
              </div>
            ))}
          </div>
        )}

        {/* Vote button */}
        {election.status === "ongoing" && (
          <div style={{ textAlign: "center", animation: "fadeUp 0.7s cubic-bezier(.16,1,.3,1)" }}>
            <button onClick={() => navigate(`/elections/${id}/vote`)}
              style={{ background: "linear-gradient(135deg,#16a34a,#22c55e)", color: "#fff", border: "none", borderRadius: 14, padding: "16px 48px", fontSize: 16, fontWeight: 700, cursor: "pointer", boxShadow: "0 4px 16px rgba(22,163,74,0.3)", fontFamily: "inherit" }}>
              🗳️ Cast Your Vote
            </button>
          </div>
        )}
      </div>
      <style>{`@keyframes fadeUp{from{opacity:0;transform:translateY(20px)}to{opacity:1;transform:translateY(0)}}`}</style>
    </Layout>
  );
}