import { useState, useEffect } from "react";
import ReactMarkdown from 'react-markdown';
// ─────────────────────────────────────────────
//  SAMPLE DATA
// ─────────────────────────────────────────────


// ─────────────────────────────────────────────
//  DESIGN TOKENS
// ─────────────────────────────────────────────
const C = {
  green:      "#15803d",
  greenLight: "#f0fdf4",
  greenBorder:"#bbf7d0",
  greenText:  "#166534",
  red:        "#dc2626",
  redLight:   "#fef2f2",
  redBorder:  "#fecaca",
  redText:    "#7f1d1d",
  amber:      "#d97706",
  amberLight: "#fffbeb",
  text:       "#111827",
  textMid:    "#374151",
  textMuted:  "#6b7280",
  textFaint:  "#9ca3af",
  border:     "#e5e7eb",
  borderFaint:"#f3f4f6",
  bg:         "#f9fafb",
  white:      "#ffffff",
};

const card = {
  background: C.white, border: `1px solid ${C.border}`,
  borderRadius: 12, padding: "1.25rem",
};
const inputStyle = {
  width: "100%", padding: "8px 12px",
  border: `1px solid ${C.border}`, borderRadius: 8,
  fontSize: 13, color: C.text, background: C.white, outline: "none",
  boxSizing: "border-box",
};

// ─────────────────────────────────────────────
//  SHARED COMPONENTS
// ─────────────────────────────────────────────
function Badge({ type, children }) {
  const map = {
    good: { bg: C.greenLight, color: C.greenText, border: C.greenBorder },
    bad:  { bg: C.redLight,   color: C.redText,   border: C.redBorder },
    up:   { bg: C.greenLight, color: C.greenText, border: C.greenBorder },
    down: { bg: C.redLight,   color: C.redText,   border: C.redBorder },
    neu:  { bg: "#f3f4f6",    color: C.textMuted,  border: C.border },
  };
  const t = map[type] || map.neu;
  return (
    <span style={{
      display: "inline-flex", alignItems: "center", gap: 3,
      fontSize: 10, padding: "2px 8px", borderRadius: 5, fontWeight: 500,
      background: t.bg, color: t.color, border: `1px solid ${t.border}`,
    }}>{children}</span>
  );
}

function StatCard({ label, value, unit, badge, badgeType, accent }) {
  return (
    <div style={{
      background: C.white, border: `1px solid ${C.border}`,
      borderRadius: 10, padding: "1rem 1.25rem",
      borderTop: accent ? `3px solid ${accent}` : undefined,
    }}>
      <div style={{ fontSize: 11, color: C.textMuted, marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.5px" }}>
        {label}
      </div>
      <div style={{ fontSize: 24, fontWeight: 600, color: C.text, lineHeight: 1, marginBottom: 6 }}>
        {value}
        {unit && <span style={{ fontSize: 13, fontWeight: 400, color: C.textFaint, marginLeft: 4 }}>{unit}</span>}
      </div>
      {badge && <Badge type={badgeType}>{badge}</Badge>}
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{ fontSize: 13, fontWeight: 600, color: C.textMid, marginBottom: "1rem", display: "flex", alignItems: "center", gap: 7 }}>
      {children}
    </div>
  );
}



const TH_STYLE = {
  textAlign: "left", color: C.textFaint, fontWeight: 500,
  padding: "0 8px 10px 0", fontSize: 11, textTransform: "uppercase", letterSpacing: "0.5px",
};
const TD_STYLE = { padding: "9px 8px 9px 0", fontSize: 12, borderBottom: `1px solid ${C.borderFaint}` };

// ─────────────────────────────────────────────
//  PAGE: DASHBOARD
// ─────────────────────────────────────────────
function Dashboard() {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    // Mengambil data statistik global dari backend
    fetch("http://127.0.0.1:8000/api/dashboard-stats")
      .then((res) => {
        if (!res.ok) throw new Error("Gagal mengambil data dari server");
        return res.json();
      })
      .then((data) => {
        setStats(data);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setError("Koneksi ke server terputus. Pastikan FastAPI sudah berjalan.");
        setLoading(false);
      });
  }, []);

  if (loading) return (
    <div style={{ padding: "3rem", textAlign: "center", color: C.textMuted }}>
      <div style={{ fontSize: "24px", marginBottom: "10px" }}>⚙️</div>
      Memuat Statistik Produksi...
    </div>
  );

  if (error) return (
    <div style={{ padding: "3rem", textAlign: "center", color: C.red }}>
      <div style={{ fontSize: "24px", marginBottom: "10px" }}>⚠️</div>
      {error}
    </div>
  );

  return (
    <div>
      <div style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: 0 }}>Production Dashboard</h1>
        <p style={{ fontSize: 13, color: C.textMuted, marginTop: 4 }}>
          Ringkasan performa lini produksi berdasarkan dataset terpusat.
        </p>
      </div>

      {/* Baris Kartu Statistik (KPI) */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: "1.5rem" }}>
        <StatCard 
          label="Total Production" 
          value={stats.total_batches} 
          accent={C.green} 
          badge="Total Unit" 
          badgeType="neu" 
        />
        <StatCard 
          label="Overall Defect Rate" 
          value={`${stats.defect_rate}%`} 
          accent={stats.defect_rate < 10 ? C.green : C.red} 
          badge="Rata-rata" 
          badgeType="neu" 
        />
        <StatCard 
          label="Success Batches" 
          value={stats.good_batches} 
          accent={C.green} 
          badge="Lulus QC" 
          badgeType="up" 
        />
        <StatCard 
          label="Failed Batches" 
          value={stats.bad_batches} 
          accent={C.red} 
          badge="Gagal QC" 
          badgeType="down" 
        />
      </div>

      {/* Tabel Data Terkini dari CSV */}
      <div style={card}>
        <div style={{ marginBottom: "1rem" }}>
          <SectionTitle>10 Riwayat Produksi Terakhir</SectionTitle>
          <p style={{ fontSize: 12, color: C.textMuted }}>Data real-time dari rekap_produksi_clustered.csv</p>
        </div>
        
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Material Description", "GK/GB Ratio", "Moisture Content", "Waste (Kg)", "Status"].map((h) => (
                  <th key={h} style={TH_STYLE}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {stats.recent_batches.map((r, index) => (
                <tr key={index} style={{ borderBottom: `1px solid ${C.borderFaint}` }}>
                  <td style={{ ...TD_STYLE, color: C.text }}>{r.Material_Description}</td>
                  <td style={{ ...TD_STYLE, color: r.Rasio_GK_GB > 2.0 ? C.red : C.textMid }}>
                    {r.Rasio_GK_GB.toFixed(2)}
                  </td>
                  <td style={{ ...TD_STYLE, color: r.GB_Kadar_Air_Mean > 5.5 ? C.red : C.textMid }}>
                    {r.GB_Kadar_Air_Mean.toFixed(1)}%
                  </td>
                  <td style={{ ...TD_STYLE, color: r.Total_Waste_Kg > 5.0 ? C.red : C.textMid }}>
                    {r.Total_Waste_Kg.toFixed(1)}
                  </td>
                  <td style={TD_STYLE}>
                    <Badge type={r.Defect_Overall === 0 ? "good" : "bad"}>
                      {r.Defect_Overall === 0 ? "✓ GOOD" : "✗ DEFECT"}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  PAGE: PREDIKSI QC
// ─────────────────────────────────────────────
function PrediksiQC() {
  const [form, setForm] = useState({ produk: "", tanggal: "", operator: "", gkgb: "", air: "", waste: "" });
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);

  const set = (k, v) => setForm(f => ({ ...f, [k]: v }));

  const handleSubmit = async () => {
    const gkgb  = parseFloat(form.gkgb);
    const air   = parseFloat(form.air);
    const waste = parseFloat(form.waste);
    
    // Validasi input
    if (isNaN(gkgb) || isNaN(air) || isNaN(waste)) {
      setError("Harap isi semua parameter produksi dengan angka.");
      return;
    }
    
    setLoading(true);
    setResult(null);
    setError(null);

    // Siapkan data pelanggaran (violations) jika melebihi batas
    const newViolations = [];
    if (gkgb > 2.0) newViolations.push({ param: "Rasio GK/GB", val: gkgb, limit: 2.0 });
    if (air > 5.5) newViolations.push({ param: "Kadar Air", val: air, limit: "5.5%" });
    if (waste > 5.0) newViolations.push({ param: "Total Waste", val: waste, limit: "5.0%" });

    try {
      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          Material_Description: form.produk || "Batch Baru",
          Rasio_GK_GB: gkgb,
          GB_Kadar_Air_Mean: air,
          Total_Waste_Kg: waste,
          // WAJIB ADA karena Backend kita minta ini sekarang
          user_query: "Berikan analisis teknis dan rekomendasi untuk parameter ini.", 
          history: [] 
        })
      });

      if (!response.ok) throw new Error("Gagal terhubung ke server FastAPI");

      const data = await response.json();
      
      setResult({
        // Pastikan format status yang dikembalikan backend cocok (misal: "bad/defect" menjadi "bad")
        status: data.prediction_status.toLowerCase().includes("bad") ? "bad" : "good",
        conf: 95, // Bisa disesuaikan jika model ML kamu mengembalikan nilai probabilitas
        violations: newViolations, // Memasukkan hasil pengecekan threshold di atas
        llm_explanation: data.llm_explanation,
        ...form, 
        gkgb, air, waste 
      });
      setError(null);
    } catch (err) {
      console.error(err);
      setError("Gagal menghubungi AI. Periksa koneksi ke FastAPI dan coba kembali.");
    } finally {
      setLoading(false);
    }
  };
  
  const handleReset = () => {
    setForm({ produk: "", tanggal: "", operator: "", gkgb: "", air: "", waste: "" });
    setResult(null);
  };

  return (
    <div style={{ maxWidth: 700 }}>
      <div style={{ marginBottom: "1.5rem" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: 0 }}>Prediksi Kualitas Batch</h1>
        <p style={{ fontSize: 13, color: C.textMuted, marginTop: 4 }}>
          Masukkan parameter produksi — model <strong>Random Forest</strong> akan memprediksi status QC secara instan.
        </p>
      </div>

      <div style={card}>
        {/* Info batch */}
        <div style={{
          fontSize: 11, fontWeight: 600, color: C.textMuted,
          textTransform: "uppercase", letterSpacing: "0.7px", marginBottom: 14,
          paddingBottom: 10, borderBottom: `1px solid ${C.borderFaint}`,
        }}>Informasi Batch</div>

        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14, marginBottom: 20 }}>
          {[
            { key: "produk",   label: "Nama Produk",       type: "text", placeholder: "Parasetamol 500mg" },
            { key: "tanggal",  label: "Tanggal Produksi",  type: "date", placeholder: "" },
            { key: "operator", label: "Nama Operator",     type: "text", placeholder: "Rina S." },
          ].map(f => (
            <div key={f.key}>
              <label style={{ fontSize: 12, color: C.textMid, fontWeight: 600, display: "block", marginBottom: 6 }}>{f.label}</label>
              <input
                type={f.type} placeholder={f.placeholder}
                value={form[f.key]} onChange={e => set(f.key, e.target.value)}
                style={inputStyle}
              />
            </div>
          ))}
        </div>

        {/* Parameter produksi */}
        <div style={{
          background: C.bg, borderRadius: 10, padding: "1.1rem",
          marginBottom: 20, border: `1px solid ${C.borderFaint}`,
        }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: C.textMuted, textTransform: "uppercase", letterSpacing: "0.7px", marginBottom: 14 }}>
            Parameter Produksi
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 14 }}>
            {[
              { key: "gkgb",  label: "Rasio GK/GB",   placeholder: "1.80", hint: "Threshold: ≤ 2.0" },
              { key: "air",   label: "Kadar Air (%)",  placeholder: "4.0",  hint: "Threshold: ≤ 5.5%" },
              { key: "waste", label: "Total Waste (%)",placeholder: "2.5",  hint: "Threshold: ≤ 5.0%" },
            ].map(p => (
              <div key={p.key}>
                <label style={{ fontSize: 12, color: C.textMid, fontWeight: 600, display: "block", marginBottom: 6 }}>{p.label}</label>
                <input
                  type="number" step="0.01" placeholder={p.placeholder}
                  value={form[p.key]} onChange={e => set(p.key, e.target.value)}
                  style={inputStyle}
                />
                <div style={{ fontSize: 10, color: C.textFaint, marginTop: 4 }}>{p.hint}</div>
              </div>
            ))}
          </div>
        </div>

        <div style={{ display: "flex", gap: 10 }}>
          <button onClick={handleSubmit} disabled={loading} style={{
            padding: "9px 22px", borderRadius: 8, fontSize: 13, fontWeight: 600,
            cursor: loading ? "default" : "pointer", border: "none",
            background: loading ? C.textFaint : C.green, color: C.white,
            transition: "background .2s",
          }}>
            {loading ? "Memproses model..." : "Prediksi Kualitas"}
          </button>
          <button onClick={handleReset} style={{
            padding: "9px 18px", borderRadius: 8, fontSize: 13,
            cursor: "pointer", border: `1px solid ${C.border}`,
            background: C.white, color: C.textMid, fontWeight: 400,
          }}>Reset</button>
        </div>
      </div>

      {/* Loading */}
      {loading && (
        <div style={{ ...card, marginTop: "1rem", textAlign: "center", padding: "2.5rem" }}>
          <div style={{ fontSize: 13, color: C.textMuted }}>
            Model Random Forest sedang menganalisis parameter...
          </div>
          <div style={{
            marginTop: 16, height: 4, background: C.borderFaint,
            borderRadius: 4, overflow: "hidden", maxWidth: 240, margin: "16px auto 0",
          }}>
            <div style={{
              height: 4, background: C.green, borderRadius: 4,
              animation: "progress 1.4s ease-in-out infinite",
              width: "60%",
            }} />
          </div>
          <style>{`@keyframes progress{0%{transform:translateX(-100%)}100%{transform:translateX(300%)}}`}</style>
        </div>
      )}

      {/* Error */}
      {error && !loading && (
        <div style={{
          ...card, marginTop: "1rem",
          background: C.redLight, border: `1px solid ${C.redBorder}`,
          borderTop: `4px solid ${C.red}`,
        }}>
          <div style={{ fontSize: 14, color: C.red, fontWeight: 600 }}>
            ⚠️ Error
          </div>
          <div style={{ fontSize: 13, color: C.redText, marginTop: 8 }}>
            {error}
          </div>
        </div>
      )}

      {/* 

      {/* Result */}
      {result && !loading && (
        <div style={{
          ...card, marginTop: "1rem",
          borderTop: `4px solid ${result.status === "good" ? C.green : C.red}`,
        }}>
          {/* Header result */}
          <div style={{ display: "flex", alignItems: "flex-start", gap: 14, marginBottom: "1.25rem" }}>
            <div style={{
              width: 52, height: 52, borderRadius: 12, flexShrink: 0,
              background: result.status === "good" ? C.greenLight : C.redLight,
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 22, border: `1px solid ${result.status === "good" ? C.greenBorder : C.redBorder}`,
            }}>
              {result.status === "good" ? "✓" : "✗"}
            </div>
            <div>
              <div style={{
                fontSize: 20, fontWeight: 700,
                color: result.status === "good" ? C.greenText : C.redText,
              }}>
                {result.status === "good" ? "GOOD — Lulus QC" : "BAD — Tidak Lulus QC"}
              </div>
              <div style={{ fontSize: 12, color: C.textMuted, marginTop: 3 }}>
                Confidence:&nbsp;
                <strong style={{ color: result.conf >= 90 ? C.green : result.conf >= 80 ? C.amber : C.red }}>
                  {result.conf}%
                </strong>
                {result.produk && <> &nbsp;·&nbsp; {result.produk}</>}
                {result.operator && <> &nbsp;·&nbsp; Operator: {result.operator}</>}
                {result.tanggal && <> &nbsp;·&nbsp; {result.tanggal}</>}
              </div>
            </div>
          </div>

          {/* Violations */}
          {result.violations.length > 0 && (
            <div style={{
              background: C.redLight, border: `1px solid ${C.redBorder}`,
              borderRadius: 8, padding: "0.85rem", marginBottom: "1rem",
            }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: C.red, marginBottom: 8 }}>
                Parameter melewati threshold:
              </div>
              {result.violations.map(v => (
                <div key={v.param} style={{ fontSize: 12, color: C.redText, marginBottom: 3 }}>
                  &bull;&nbsp; {v.param}: <strong>{v.val.toFixed(2)}</strong> (limit: {v.limit})
                </div>
              ))}
            </div>
          )}

          {/* Recommendation */}
          <div style={{
            background: result.status === "good" ? C.greenLight : C.amberLight,
            border: `1px solid ${result.status === "good" ? C.greenBorder : "#fcd34d"}`,
            borderRadius: 8, padding: "0.85rem",
            fontSize: 13, color: result.status === "good" ? C.greenText : "#78350f",
            lineHeight: 1.7,
          }}>
            <strong>Rekomendasi sistem:</strong><br />
            {result.status === "good"
              ? `Parameter produksi ${result.produk || "batch ini"} berada dalam batas normal. Batch dapat dilanjutkan ke tahap pengemasan. Pantau konsistensi parameter pada batch berikutnya untuk menjaga performa.`
              : `Batch ${result.produk || "ini"} terdeteksi memiliki cacat kualitas. Segera isolasi batch dan lakukan investigasi pada ${result.violations.map(v => v.param).join(" dan ")}. Periksa kalibrasi sensor dan kondisi mesin produksi sebelum melanjutkan.`
            }
          </div>

          {/* Param summary */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 10, marginTop: "1rem" }}>
            {[
              { label: "Rasio GK/GB", val: result.gkgb.toFixed(2), limit: 2.0, ok: result.gkgb <= 2.0 },
              { label: "Kadar Air",   val: `${result.air.toFixed(1)}%`, limit: "5.5%", ok: result.air <= 5.5 },
              { label: "Total Waste", val: `${result.waste.toFixed(1)}%`, limit: "5.0%", ok: result.waste <= 5.0 },
            ].map(m => (
              <div key={m.label} style={{
                background: m.ok ? C.greenLight : C.redLight,
                border: `1px solid ${m.ok ? C.greenBorder : C.redBorder}`,
                borderRadius: 8, padding: "0.7rem",
                textAlign: "center",
              }}>
                <div style={{ fontSize: 10, color: C.textMuted, marginBottom: 4 }}>{m.label}</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: m.ok ? C.greenText : C.redText }}>{m.val}</div>
                <div style={{ fontSize: 10, color: C.textFaint, marginTop: 2 }}>limit: {m.limit}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─────────────────────────────────────────────
//  PAGE: RIWAYAT BATCH
// ─────────────────────────────────────────────
function RiwayatBatch() {
  const [search,      setSearch]      = useState("");
  const [statusF,     setStatusF]     = useState("all");
  const [data,        setData]        = useState(null);
  const [loading,     setLoading]     = useState(true);
  const [error,       setError]       = useState(null);

  const pageSize = 50;

  // Fetch data saat status filter berubah
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const response = await fetch(`http://127.0.0.1:8000/api/batch-history?skip=0&limit=${pageSize}&status=${statusF}`);
        
        if (!response.ok) throw new Error("Gagal fetch data dari server");
        const json = await response.json();
        setData(json);
      } catch (err) {
        console.error(err);
        setError("Koneksi ke server terputus. Pastikan FastAPI sudah berjalan.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [statusF]);

  // Filter data berdasarkan search
  const filtered = data?.batches?.filter(b => {
    const q = search.toLowerCase();
    return b.id.toLowerCase().includes(q) || 
           b.material.toLowerCase().includes(q);
  }) || [];

  const goodCount = filtered.filter(b => b.defect === 0).length;
  const badCount  = filtered.filter(b => b.defect === 1).length;

  if (loading) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: C.textMuted }}>
        <div style={{ fontSize: "24px", marginBottom: "10px" }}>⚙️</div>
        Memuat Riwayat Batch...
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: "3rem", textAlign: "center", color: C.red }}>
        <div style={{ fontSize: "24px", marginBottom: "10px" }}>⚠️</div>
        {error}
      </div>
    );
  }

  return (
    <div>
      <div style={{ marginBottom: "1.25rem" }}>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: C.text, margin: 0 }}>Riwayat Batch</h1>
        <p style={{ fontSize: 13, color: C.textMuted, marginTop: 4 }}>Seluruh data produksi yang telah tercatat dan dianalisis sistem.</p>
      </div>

      {/* Summary mini cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10, marginBottom: "1rem" }}>
        <div style={{ ...card, padding: "0.85rem 1rem" }}>
          <div style={{ fontSize: 10, color: C.textFaint, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>Total Record</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: C.text }}>{data?.total || 0}</div>
        </div>
        <div style={{ ...card, padding: "0.85rem 1rem", borderTop: `3px solid ${C.green}` }}>
          <div style={{ fontSize: 10, color: C.textFaint, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>Good Status</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: C.green }}>
            {data?.batches ? data.batches.filter(b => b.defect === 0).length : 0}
          </div>
        </div>
        <div style={{ ...card, padding: "0.85rem 1rem", borderTop: `3px solid ${C.red}` }}>
          <div style={{ fontSize: 10, color: C.textFaint, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>Defect Status</div>
          <div style={{ fontSize: 22, fontWeight: 700, color: C.red }}>
            {data?.batches ? data.batches.filter(b => b.defect === 1).length : 0}
          </div>
        </div>
      </div>

      <div style={card}>
        {/* Filter bar */}
        <div style={{ display: "flex", gap: 10, marginBottom: "1rem", flexWrap: "wrap", alignItems: "center" }}>
          <input
            placeholder="Cari batch ID atau material..."
            value={search} onChange={e => setSearch(e.target.value)}
            style={{ ...inputStyle, width: 280 }}
          />
          <div style={{ display: "flex", gap: 6 }}>
            {["all", "good", "bad"].map(f => (
              <button key={f} onClick={() => setStatusF(f)} style={{
                padding: "6px 14px", borderRadius: 20,
                border: `1px solid ${f === statusF ? C.green : C.border}`,
                background: f === statusF ? C.green : C.white,
                color: f === statusF ? C.white : C.textMuted,
                fontSize: 12, cursor: "pointer", fontWeight: f === statusF ? 600 : 400,
              }}>
                {f === "all" ? "Semua" : f === "good" ? "✓ Good" : "✗ Defect"}
              </button>
            ))}
          </div>
          <span style={{ fontSize: 12, color: C.textFaint, marginLeft: "auto" }}>
            {filtered.length} entri &nbsp;·&nbsp;
            <span style={{ color: C.green }}>{goodCount} good</span> &nbsp;·&nbsp;
            <span style={{ color: C.red }}>{badCount} defect</span>
          </span>
        </div>

        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse" }}>
            <thead>
              <tr>
                {["Batch ID", "Material", "GK/GB", "Kadar Air", "Waste", "Status", "Cluster"].map(h => (
                  <th key={h} style={TH_STYLE}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={7} style={{ textAlign: "center", padding: "2.5rem", color: C.textFaint, fontSize: 13 }}>
                    Tidak ada data yang cocok
                  </td>
                </tr>
              ) : filtered.map(b => (
                <tr key={b.id} style={{ transition: "background .1s" }}
                  onMouseEnter={e => e.currentTarget.style.background = C.bg}
                  onMouseLeave={e => e.currentTarget.style.background = "transparent"}
                >
                  <td style={{ ...TD_STYLE, fontFamily: "monospace", fontSize: 11, color: C.textMid }}>{b.id}</td>
                  <td style={{ ...TD_STYLE, color: C.text, fontSize: 12 }}>{b.material}</td>
                  <td style={{ ...TD_STYLE, color: b.gk_gb > 2.0 ? C.red : C.textMid, fontWeight: b.gk_gb > 2.0 ? 600 : 400 }}>
                    {b.gk_gb.toFixed(2)}
                  </td>
                  <td style={{ ...TD_STYLE, color: b.air > 5.5 ? C.red : C.textMid, fontWeight: b.air > 5.5 ? 600 : 400 }}>
                    {b.air.toFixed(1)}%
                  </td>
                  <td style={{ ...TD_STYLE, color: b.waste > 5.0 ? C.red : C.textMid, fontWeight: b.waste > 5.0 ? 600 : 400 }}>
                    {b.waste.toFixed(1)}%
                  </td>
                  <td style={TD_STYLE}>
                    <Badge type={b.defect === 0 ? "good" : "bad"}>
                      {b.defect === 0 ? "✓ Good" : "✗ Defect"}
                    </Badge>
                  </td>
                  <td style={{ ...TD_STYLE, fontSize: 11, color: C.textMuted }}>{b.cluster}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination info */}
        {data && data.total > pageSize && (
          <div style={{ marginTop: "1rem", textAlign: "center", fontSize: 12, color: C.textMuted }}>
            Menampilkan {filtered.length} dari {data.total} total records
          </div>
        )}
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  PAGE: AI ANALYST
// ─────────────────────────────────────────────
function AIAnalyst() {
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  
  // State untuk menyimpan semua sesi percakapan
  const [sessions, setSessions] = useState(() => {
    const saved = localStorage.getItem("pharma_sessions");
    // Gunakan fungsi pengembalian untuk menghindari Date.now() saat render ulang
    return saved ? JSON.parse(saved) : [{ id: Date.now(), title: "Percakapan Baru", messages: [] }];
  });

  const [activeSessionId, setActiveSessionId] = useState(sessions[0]?.id);

  const activeSession = sessions.find(s => s.id === activeSessionId) || sessions[0];

  useEffect(() => {
    localStorage.setItem("pharma_sessions", JSON.stringify(sessions));
  }, [sessions]);

  // Fungsi untuk membuat chat baru
  const createNewChat = () => {
    const newId = Date.now();
    const newSession = { id: newId, title: "Percakapan Baru", messages: [] };
    setSessions([newSession, ...sessions]);
    setActiveSessionId(newId);
  };

  const sendMessage = async (e) => {
    if (e) e.preventDefault();
    if (!input.trim()) return;

    const userMsg = { role: "user", content: input };
    const updatedMessages = [...activeSession.messages, userMsg];

    // Update judul chat berdasarkan input pertama
    const updatedSessions = sessions.map(s => 
      s.id === activeSessionId 
        ? { ...s, messages: updatedMessages, title: s.messages.length === 0 ? input.substring(0, 25) + "..." : s.title } 
        : s
    );
    
    setSessions(updatedSessions);
    setInput("");
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:8000/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_query: input,
          history: updatedMessages,
          Material_Description: "General Inquiry",
          Rasio_GK_GB: 0, GB_Kadar_Air_Mean: 0, Total_Waste_Kg: 0
        })
      });

      const data = await response.json();
      const aiMsg = { role: "assistant", content: data.llm_explanation };
      
      setSessions(prev => prev.map(s => 
        s.id === activeSessionId ? { ...s, messages: [...updatedMessages, aiMsg] } : s
      ));
    } catch (err) {
      console.error("Gagal terhubung ke server:", err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ display: "flex", height: "100vh", background: C.background }}>
      {/* SIDEBAR RIWAYAT (ULTRA SLIM) */}
      <div style={{ 
        width: "180px", // Diperkecil dari 220px ke 180px
        borderRight: `1px solid ${C.borderFaint}`, 
        display: "flex", 
        flexDirection: "column", 
        gap: "5px", 
        padding: "10px 5px" // Padding kiri-kanan diperkecil
      }}>
  
  <button onClick={createNewChat} style={{
    padding: "6px 10px", // Lebih pendek
    borderRadius: "6px", 
    background: "transparent", 
    color: C.green, 
    border: `1px solid ${C.green}`, 
    fontSize: "11px", // Ukuran font diperkecil
    fontWeight: 600, 
    cursor: "pointer",
    marginBottom: "12px",
    transition: "0.2s",
    width: "100%"
  }}>
    + Chat Baru
  </button>
  
  <div style={{ overflowY: "auto", flex: 1, display: "flex", flexDirection: "column", gap: "2px" }}>
    <p style={{ 
      fontSize: "9px", // Sangat kecil agar rapi
      color: C.textMuted, 
      fontWeight: 700, 
      paddingLeft: "8px", 
      marginBottom: "4px", 
      letterSpacing: "0.8px",
      textTransform: "uppercase"
    }}>
      Riwayat
    </p>
    
    {sessions.map(s => (
      <div 
        key={s.id} 
        onClick={() => setActiveSessionId(s.id)}
        style={{
          padding: "6px 8px", // Padding sangat minimal
          borderRadius: "5px", 
          fontSize: "11.5px", // Font disesuaikan agar tetap terbaca
          cursor: "pointer",
          display: "flex", 
          justifyContent: "space-between", 
          alignItems: "center",
          background: s.id === activeSessionId ? C.borderFaint : "transparent",
          color: s.id === activeSessionId ? C.green : C.text,
          transition: "0.2s"
        }}
      >
        <span style={{ 
          whiteSpace: "nowrap", 
          overflow: "hidden", 
          textOverflow: "ellipsis", 
          width: "130px" // Menyesuaikan dengan lebar sidebar yang baru
        }}>
          📄 {s.title}
        </span>

        <button 
          onClick={(e) => {
            e.stopPropagation();
            if (window.confirm("Hapus percakapan ini?")) {
              const updatedSessions = sessions.filter(s2 => s2.id !== s.id);
              
              if (updatedSessions.length === 0) {
                const newId = Date.now();
                const newS = [{ id: newId, title: "Percakapan Baru", messages: [] }];
                setSessions(newS);
                setActiveSessionId(newId);
              } else {
                setSessions(updatedSessions);
                if (s.id === activeSessionId) {
                  setActiveSessionId(updatedSessions[0].id);
                }
              }
            }
          }}
          style={{ 
            background: "none", 
            border: "none", 
            color: C.textFaint, 
            cursor: "pointer", 
            fontSize: "12px",
            padding: "0 2px"
          }}
        >
          ⋮
        </button>
      </div>
    ))}
  </div>
</div>

      {/* AREA CHAT UTAMA */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", minWidth: 0 }}>
        <div style={{ flex: 1, overflowY: "auto", padding: "15px", background: C.borderFaint, borderRadius: "16px", marginBottom: "15px" }}>
          {activeSession.messages.length === 0 ? (
            <div style={{ textAlign: "center", marginTop: "15%", color: C.textMuted }}>
              <div style={{ fontSize: "30px", marginBottom: "10px" }}>💊</div>
              <p style={{ fontSize: "14px", fontWeight: 500 }}>Halo, Anis! Ada yang bisa PharmaSight AI bantu hari ini?</p>
              <p style={{ fontSize: "12px", opacity: 0.7 }}>Tanyakan hasil QC, tren produksi, atau analisis batch tertentu.</p>
            </div>
          ) : (
            activeSession.messages.map((m, i) => (
              <div key={i} style={{ display: "flex", justifyContent: m.role === "user" ? "flex-end" : "flex-start", marginBottom: "20px" }}>
                <div style={{ 
                  maxWidth: "85%", padding: "12px 16px", borderRadius: "14px", fontSize: "13px",
                  background: m.role === "user" ? C.green : C.white,
                  color: m.role === "user" ? "white" : C.text,
                  boxShadow: "0 2px 8px rgba(0,0,0,0.04)",
                  lineHeight: "1.6"
                }}>
                  <div style={{ fontWeight: 800, fontSize: "10px", marginBottom: "6px", opacity: 0.6, letterSpacing: "0.5px" }}>
                    {m.role === "user" ? "ANDA" : "PHARMASIGHT AI ANALYST"}
                  </div>
                  
                  {/* Markdown Renderer agar teks poin-poin tidak numpuk */}
                  <div style={{ textAlign: "justify" }} className="markdown-container">
                    <ReactMarkdown>{m.content}</ReactMarkdown>
                  </div>
                </div>
              </div>
            ))
          )}
          {loading && <div style={{ fontSize: "11px", color: C.textMuted, marginLeft: "10px" }}>AI sedang memproses data...</div>}
        </div>

        {/* Input area */}
        <form onSubmit={sendMessage} style={{ display: "flex", gap: "10px", paddingBottom: "5px" }}>
          <input 
            value={input} onChange={(e) => setInput(e.target.value)}
            placeholder="Ketik pesan analisis di sini..."
            style={{ flex: 1, padding: "12px 16px", borderRadius: "10px", border: `1px solid ${C.border}`, fontSize: "13px", outline: "none" }}
          />
          <button type="submit" disabled={loading || !input.trim()} style={{
            padding: "0 25px", background: loading ? C.textFaint : C.green, color: "white", 
            border: "none", borderRadius: "10px", fontWeight: 600, cursor: "pointer", transition: "0.3s"
          }}>
            {loading ? "..." : "Kirim"}
          </button>
        </form>
      </div>
    </div>
  );
}

// ─────────────────────────────────────────────
//  APP SHELL
// ─────────────────────────────────────────────
const NAV = [
  { key: "dashboard", label: "Dashboard",     icon: "▦" },
  { key: "prediksi",  label: "Prediksi QC",   icon: "◎" },
  { key: "riwayat",   label: "Riwayat Batch", icon: "≡" },
  { key: "analyst",   label: "AI Analyst",    icon: "⬡" },
];

export default function PharmaSight() {
  const [page, setPage] = useState("dashboard");

  return (
    <div style={{
      display: "flex", minHeight: 680,
      borderRadius: 16, overflow: "hidden",
      border: `1px solid ${C.border}`,
      fontFamily: "var(--font-sans)",
      background: C.bg,
    }}>
      {/* Sidebar */}
      <div style={{
        width: 220, background: C.white,
        borderRight: `1px solid ${C.border}`,
        display: "flex", flexDirection: "column",
        flexShrink: 0,
      }}>
        {/* Logo */}
        <div style={{ padding: "1.25rem", borderBottom: `1px solid ${C.borderFaint}` }}>
          <div style={{ fontSize: 17, fontWeight: 800, color: C.green, letterSpacing: -0.5 }}>⬡ PharmaSight</div>
          <div style={{ fontSize: 10, color: C.textFaint, letterSpacing: "1px", textTransform: "uppercase", marginTop: 3 }}>
            Production QC Monitor
          </div>
        </div>

        {/* Nav section */}
        <div style={{ padding: "0.75rem 0" }}>
          <div style={{ fontSize: 10, color: C.textFaint, letterSpacing: "0.8px", textTransform: "uppercase", padding: "0.5rem 1.25rem 0.25rem" }}>
            Menu Utama
          </div>
          {NAV.map(n => {
            const active = page === n.key;
            return (
              <div key={n.key} onClick={() => setPage(n.key)} style={{
                display: "flex", alignItems: "center", gap: 10,
                padding: "0.6rem 1.25rem",
                fontSize: 13, fontWeight: active ? 600 : 400,
                cursor: "pointer",
                color: active ? C.green : C.textMuted,
                background: active ? C.greenLight : "transparent",
                borderLeft: `3px solid ${active ? C.green : "transparent"}`,
                transition: "all .15s",
              }}>
                <span style={{ fontSize: 16, lineHeight: 1 }}>{n.icon}</span>
                <span>{n.label}</span>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div style={{ marginTop: "auto", padding: "1rem 1.25rem", borderTop: `1px solid ${C.borderFaint}` }}>
          <div style={{ fontSize: 10, color: C.textFaint, textTransform: "uppercase", letterSpacing: "0.5px", marginBottom: 4 }}>
            Model aktif
          </div>
          <div style={{ fontSize: 12, color: C.textMid, fontWeight: 600 }}>Random Forest</div>
          <div style={{ fontSize: 11, color: C.textFaint }}>+ LLaMA-3 · ChromaDB RAG</div>
          <div style={{ display: "flex", alignItems: "center", gap: 5, marginTop: 8 }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: C.green }} />
            <span style={{ fontSize: 10, color: C.green }}>System online</span>
          </div>
        </div>
      </div>

      {/* Main content */}
      <div style={{ flex: 1, padding: "1.5rem", overflowY: "auto" }}>
        {page === "dashboard" && <Dashboard />}
        {page === "prediksi"  && <PrediksiQC />}
        {page === "riwayat"   && <RiwayatBatch />}
        {page === "analyst"   && <AIAnalyst />}
      </div>
    </div>
  );
}
