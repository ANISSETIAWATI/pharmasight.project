"""
================================================================
  SNIPPET: Integrasi AI Analyst ke 05_dashboard.py
  
  Tempel kode ini ke dalam file 05_dashboard.py kamu
  pada bagian Tab AI Analyst.
================================================================
"""

# ── Di bagian import atas 05_dashboard.py ────────────────────
import streamlit as st
import pandas as pd
from pathlib import Path

# Import AI analyst (pastikan 07_ai_analyst.py ada di folder yang sama)
try:
    import sys
    sys.path.append(".")
    from ai_analyst_07 import get_analyst_for_streamlit
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False


# ── Di bagian awal app (setelah st.set_page_config) ──────────
@st.cache_resource(show_spinner="Memuat AI Analyst...")
def load_ai_analyst():
    """Cache RAG chain agar tidak rebuild setiap rerun."""
    if not AI_AVAILABLE:
        return None, None
    analyze_fn, query_fn = get_analyst_for_streamlit()
    return analyze_fn, query_fn


# ── Tab AI Analyst ───────────────────────────────────────────
def render_ai_analyst_tab():
    """
    Tempel fungsi ini ke dalam 05_dashboard.py dan panggil
    di dalam blok: with tab_ai: render_ai_analyst_tab()
    """
    st.header("🤖 AI Analyst")
    st.caption("Powered by RAG + LLM | PJK-GM016")
    
    analyze_fn, query_fn = load_ai_analyst()
    
    if not AI_AVAILABLE or analyze_fn is None:
        st.error("❌ AI Analyst tidak tersedia. Pastikan 07_ai_analyst.py dan RAG DB sudah disiapkan.")
        st.code("python 06_build_rag.py  # Build knowledge base dulu")
        return
    
    # ── Sub-tab ──────────────────────────────────────────────
    subtab1, subtab2, subtab3 = st.tabs([
        "🔍 Analisis Batch Baru",
        "💬 Tanya AI",
        "📊 Ringkasan High-Risk"
    ])
    
    # ── Sub-tab 1: Analisis Batch Baru ───────────────────────
    with subtab1:
        st.subheader("Analisis Batch Baru")
        st.info("Masukkan parameter batch, lalu klik Analisis untuk mendapatkan insight AI.")
        
        col1, col2 = st.columns(2)
        with col1:
            gb_yield    = st.number_input("GB_Yield_Total (kg)",    value=425.72, step=1.0)
            gk_yield    = st.number_input("GK_Yield_Total (kg)",    value=908.38, step=1.0)
            rasio       = st.number_input("Rasio_GK_GB",            value=2.13,   step=0.01)
            kadar_air   = st.number_input("GB_Kadar_Air_Mean (%)",  value=5.42,   step=0.01)
            cetak_yield = st.number_input("Cetak_Yield_Kg (kg)",    value=712.0,  step=1.0)
        with col2:
            cetak_pct   = st.number_input("Cetak_Pct_Teoritis",     value=2.82,   step=0.01)
            kemas_pct   = st.number_input("Kemas_Pct_Teoritis",     value=2.78,   step=0.01)
            total_waste = st.number_input("Total_Waste_Kg (kg)",    value=0.0,    step=0.1)
            cetak_dur   = st.number_input("Cetak_Durasi_Hari",      value=1.0,    step=0.5)
            kemas_dur   = st.number_input("Kemas_Durasi_Hari",      value=1.0,    step=0.5)
        
        st.divider()
        st.subheader("Hasil Prediksi Model (dari 03_modeling.py)")
        col3, col4, col5 = st.columns(3)
        with col3:
            rf_pred = st.selectbox("Prediksi RF", [0, 1], format_func=lambda x: "✅ Normal" if x == 0 else "⚠️ Defect")
        with col4:
            rf_prob = st.slider("Probabilitas Defect", 0.0, 1.0, 0.12, 0.01)
        with col5:
            cluster = st.selectbox("Klaster K-Means", [0, 1, 2],
                                   format_func=lambda x: {0: "K0 – Medium Risk", 1: "K1 – Low Risk", 2: "K2 – High Risk"}[x])
        
        if st.button("🔍 Analisis dengan AI", type="primary", use_container_width=True):
            batch_data = {
                "GB_Yield_Total":     gb_yield,
                "GK_Yield_Total":     gk_yield,
                "Rasio_GK_GB":        rasio,
                "GB_Kadar_Air_Mean":  kadar_air,
                "Cetak_Yield_Kg":     cetak_yield,
                "Cetak_Pct_Teoritis": cetak_pct,
                "Kemas_Pct_Teoritis": kemas_pct,
                "Total_Waste_Kg":     total_waste,
                "Cetak_Durasi_Hari":  cetak_dur,
                "Kemas_Durasi_Hari":  kemas_dur,
            }
            
            with st.spinner("AI sedang menganalisis batch..."):
                result = analyze_fn(batch_data, rf_pred, rf_prob, cluster)
            
            # Tampilkan hasil
            status_color = "🔴" if rf_pred == 1 else "🟢"
            st.markdown(f"### {status_color} Hasil Analisis AI")
            st.markdown(result["analysis"])
            
            with st.expander("📚 Dokumen Referensi yang Digunakan AI"):
                for i, src in enumerate(result.get("source_documents", []), 1):
                    st.text(f"[{i}] {src}")
    
    # ── Sub-tab 2: Tanya AI ──────────────────────────────────
    with subtab2:
        st.subheader("Tanya AI Analyst")
        
        # Contoh pertanyaan
        st.caption("Contoh pertanyaan:")
        example_qs = [
            "Apa faktor utama penyebab defect?",
            "Bagaimana cara menurunkan Kemas_Durasi_Hari?",
            "Klaster 2 high risk, apa yang harus dilakukan?",
            "Jelaskan arti nilai Rasio_GK_GB = 0.6",
        ]
        cols = st.columns(2)
        for i, q in enumerate(example_qs):
            if cols[i % 2].button(q, key=f"example_{i}"):
                st.session_state["ai_question"] = q
        
        question = st.text_area(
            "Pertanyaanmu:",
            value=st.session_state.get("ai_question", ""),
            height=100,
            placeholder="Contoh: Mengapa Kemas_Pct_Teoritis sangat berpengaruh terhadap defect?"
        )
        
        if st.button("💬 Tanya AI", type="primary") and question:
            with st.spinner("AI sedang menjawab..."):
                result = query_fn(question)
            
            st.markdown("### 🤖 Jawaban AI")
            st.markdown(result["answer"])
            
            with st.expander("Sumber Referensi"):
                for src in result.get("sources", []):
                    st.caption(f"📄 {src}")
    
    # ── Sub-tab 3: Ringkasan High-Risk ───────────────────────
    with subtab3:
        st.subheader("Analisis Batch High-Risk")
        
        csv_path = st.text_input(
            "Path CSV Clustered:",
            value="./data/rekap_produksi_clustered.csv"
        )
        
        if st.button("📊 Generate Ringkasan AI", type="primary"):
            if not Path(csv_path).exists():
                st.error(f"File tidak ditemukan: {csv_path}")
            else:
                with st.spinner("AI sedang menganalisis batch high-risk..."):
                    from ai_analyst_07 import get_high_risk_summary, build_rag_chain
                    rc, _ = build_rag_chain()
                    summary = get_high_risk_summary(csv_path, rc)
                
                st.markdown("### 🔴 Ringkasan Batch High-Risk")
                st.markdown(summary)


# ── Contoh integrasi ke dalam tab utama dashboard ────────────
# Di dalam main() 05_dashboard.py:
#
# tab1, tab2, tab3, tab4, tab5 = st.tabs([
#     "📊 Overview",
#     "📈 Monitoring",
#     "🎯 Prediksi",
#     "🔵 Clustering",
#     "🤖 AI Analyst"    ← tambahkan tab ini
# ])
#
# with tab5:
#     render_ai_analyst_tab()
