# FILE: ui.py
# VERSION: v106.0 (Complete & Robust)
# DATE: 2026-01-11

import streamlit as st
import base64
import os

# --- GESTIONE SFONDI (La funzione che mancava) ---
def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f: data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError: return None

def set_backgrounds(main_bg, sidebar_bg):
    """Imposta lo sfondo per la pagina principale e la sidebar"""
    if os.path.exists(main_bg):
        bin_str = get_base64_of_bin_file(main_bg)
        if bin_str:
            st.markdown(f"""<style>.stApp {{ background-image: url(data:image/jpg;base64,{bin_str}) !important; background-size: cover !important; background-attachment: fixed !important; }}</style>""", unsafe_allow_html=True)
    
    if os.path.exists(sidebar_bg):
        bin_str_side = get_base64_of_bin_file(sidebar_bg)
        if bin_str_side:
            st.markdown(f"""<style>section[data-testid="stSidebar"] {{ background-image: url(data:image/jpg;base64,{bin_str_side}) !important; background-size: cover !important; }} section[data-testid="stSidebar"] > div:first-child {{ background-color: rgba(255, 255, 255, 0.95); }}</style>""", unsafe_allow_html=True)

def load_css():
    """Carica gli stili CSS per le card e i risultati"""
    st.markdown("""
    <style>
        .question-card {
            background-color: #ffffff; padding: 20px; border-radius: 15px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); border-left: 5px solid #003366;
            margin-bottom: 20px; color: #333;
        }
        .metric-container { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .metric-box {
            background: white; padding: 10px 20px; border-radius: 10px;
            text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-weight: bold; color: #555;
        }
        .res-box {
            padding: 15px; border-radius: 10px; margin-bottom: 10px;
            font-weight: bold; border: 1px solid #ddd;
        }
        .res-correct { background-color: #d4edda; color: #155724; border-color: #c3e6cb; }
        .res-wrong { background-color: #f8d7da; color: #721c24; border-color: #f5c6cb; }
        .res-neutral { background-color: #f8f9fa; color: #383d41; }
        
        .exam-pass { text-align: center; color: #28a745; padding: 20px; background: #e8f5e9; border-radius: 15px; }
        .exam-fail { text-align: center; color: #dc3545; padding: 20px; background: #fbe9eb; border-radius: 15px; }
        .review-end { text-align: center; color: #004085; padding: 20px; background: #cce5ff; border-radius: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- COMPONENTI GRAFICI ---
def draw_rank_box(rank_name, mastered_count, next_target):
    st.markdown(f"""
    <div style="background-color:#e3f2fd; padding:15px; border-radius:10px; margin-bottom:15px; text-align:center; border:2px solid #90caf9;">
        <div style="font-size:1.2em; color:#1565c0; font-weight:bold;">{rank_name}</div>
        <div style="font-size:0.9em; color:#555;">Domande Dominate: <b>{mastered_count}</b> / {next_target}</div>
    </div>
    """, unsafe_allow_html=True)

def draw_question_card(q_id, topic, subtopic, text):
    st.markdown(f"""
    <div class="question-card">
        <div style="color:#888; font-size:0.8em; margin-bottom:5px;">{q_id} • {topic}</div>
        <div style="color:#555; font-size:0.9em; font-style:italic; margin-bottom:10px;">{subtopic}</div>
        <div style="font-size:1.3em; font-weight:600; color:#222; line-height:1.4;">{text}</div>
    </div>
    """, unsafe_allow_html=True)

def draw_result_option(text, is_correct, is_selected, last_answer_was_correct):
    style = "res-neutral"
    icon = "⚪"
    
    if is_correct:
        style = "res-correct"
        icon = "✅"
    elif is_selected and not is_correct:
        style = "res-wrong"
        icon = "❌"
    
    st.markdown(f'<div class="res-box {style}">{icon} {text}</div>', unsafe_allow_html=True)

# --- FUNZIONE STATISTICHE BLINDATA (Anti-Crash) ---
def draw_stats_dashboard_advanced(df_stats):
    st.markdown("## 📊 Il Tuo Libretto")
    
    # Se il dataframe è vuoto o None, esce subito
    if df_stats is None or df_stats.empty:
        st.info("Fai qualche quiz per vedere i dati.")
        return

    # Calcolo metriche con protezione (usa 0 se la colonna manca)
    try:
        tot = df_stats['Totali'].sum() if 'Totali' in df_stats.columns else 0
        svolte = df_stats['Svolte'].sum() if 'Svolte' in df_stats.columns else 0
        giuste = df_stats['Giuste'].sum() if 'Giuste' in df_stats.columns else 0
        prec = (giuste / svolte * 100) if svolte > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Avanzamento", f"{int(svolte/tot*100)}%", f"{svolte}/{tot}")
        c2.metric("Precisione", f"{prec:.0f}%")
        
        # Punto debole (solo se esistono le colonne necessarie)
        if 'Svolte' in df_stats.columns and '% Precisione' in df_stats.columns:
            df_active = df_stats[df_stats['Svolte'] > 0]
            if not df_active.empty:
                weakest = df_active.sort_values(by='% Precisione').iloc[0]
                c3.metric("Punto Debole", f"{weakest['% Precisione']:.0f}%", weakest['Argomento'])
    except Exception as e:
        st.error(f"Errore calcolo metriche: {e}")

    # Visualizzazione tabella PROTETTA (Fix per KeyError)
    try:
        # Tenta di colorare solo le colonne che esistono davvero
        target_cols = ['% Precisione', '% Completamento']
        valid_cols = [c for c in target_cols if c in df_stats.columns]
        
        st.dataframe(
            df_stats.style.background_gradient(cmap="RdYlGn", subset=valid_cols),
            use_container_width=True,
            hide_index=True
        )
    except Exception:
        # Se fallisce lo stile, mostra la tabella semplice (così non crasha mai)
        st.dataframe(df_stats, use_container_width=True, hide_index=True)