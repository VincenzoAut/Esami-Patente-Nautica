# FILE: ui.py
# VERSION: v111.0 (Tablet & Visibility Optimization)
# DATE: 2026-01-11

import streamlit as st
import base64
import os

# --- GESTIONE SFONDI ---
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
    """
    Carica gli stili CSS.
    Include FIX per TABLET (Forza tema chiaro ad alto contrasto).
    """
    st.markdown("""
    <style>
        /* --- FIX TABLET & VISIBILITA' --- */
        
        /* 1. Forza testo nero globale (risolve menu illeggibili) */
        html, body, [class*="css"], [data-testid="stSidebar"] {
            color: #000000 !important; 
            font-family: sans-serif;
        }

        /* 2. Bottoni: Sfondo Bianco e Bordo (Niente più bottoni neri) */
        div.stButton > button {
            background-color: #ffffff !important;
            color: #000000 !important;
            border: 1px solid #cccccc !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1) !important;
            font-weight: bold !important;
        }
        div.stButton > button:hover {
            border-color: #003366 !important;
            color: #003366 !important;
            background-color: #f0f8ff !important;
        }
        div.stButton > button:active {
            background-color: #e3f2fd !important;
        }
        
        /* Bottoni Primari (es. Entra, Prossima) - Blu scuro */
        div.stButton > button[kind="primary"] {
            background-color: #003366 !important;
            color: #ffffff !important;
            border: none !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background-color: #004080 !important;
        }

        /* 3. Menu a tendina e Input (Sfondo bianco obbligatorio) */
        .stSelectbox div[data-baseweb="select"] > div,
        .stTextInput input, 
        .stTextArea textarea {
            background-color: #ffffff !important;
            color: #000000 !important;
            border-color: #cccccc !important;
        }
        /* Testo dentro le tendine */
        div[data-baseweb="select"] span {
            color: #000000 !important;
        }
        /* Etichette (Label) dei menu */
        .stSelectbox label, .stTextInput label, .stRadio label {
            color: #000000 !important;
            font-weight: 600 !important;
            background-color: rgba(255,255,255,0.7); /* Leggero sfondo per leggere su img */
            padding: 2px 5px;
            border-radius: 4px;
        }

        /* 4. Radio Button (Scelta Quiz) */
        div[role="radiogroup"] label {
            color: #000000 !important;
        }

        /* --- STILI CARD E RISULTATI --- */
        .question-card {
            background-color: #ffffff !important; /* Forza BIanco */
            padding: 20px; 
            border-radius: 15px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important; /* Ombra più forte per contrasto */
            border-left: 8px solid #003366;
            margin-bottom: 20px; 
            color: #000000 !important; /* Testo Nero */
        }
        
        .metric-container { display: flex; justify-content: space-around; margin-bottom: 20px; }
        .metric-box {
            background: white !important; 
            padding: 10px 20px; 
            border-radius: 10px;
            text-align: center; 
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            font-weight: bold; 
            color: #333 !important;
            border: 1px solid #ddd;
        }
        
        .res-box {
            padding: 15px; border-radius: 10px; margin-bottom: 10px;
            font-weight: bold; border: 1px solid #ddd;
            color: #000 !important; /* Testo nero anche nei risultati */
        }
        .res-correct { background-color: #d4edda !important; color: #155724 !important; border-color: #c3e6cb; }
        .res-wrong { background-color: #f8d7da !important; color: #721c24 !important; border-color: #f5c6cb; }
        .res-neutral { background-color: #f8f9fa !important; color: #383d41 !important; }
        
        .exam-pass { text-align: center; color: #28a745 !important; padding: 20px; background: #e8f5e9 !important; border-radius: 15px; border: 1px solid #c3e6cb; }
        .exam-fail { text-align: center; color: #dc3545 !important; padding: 20px; background: #fbe9eb !important; border-radius: 15px; border: 1px solid #f5c6cb; }
        .review-end { text-align: center; color: #004085 !important; padding: 20px; background: #cce5ff !important; border-radius: 15px; border: 1px solid #b8daff; }
    </style>
    """, unsafe_allow_html=True)

# --- COMPONENTI GRAFICI ---
def draw_rank_box(rank_name, mastered_count, next_target):
    st.markdown(f"""
    <div style="background-color:#e3f2fd; padding:15px; border-radius:10px; margin-bottom:15px; text-align:center; border:2px solid #90caf9; color:#000;">
        <div style="font-size:1.2em; color:#1565c0; font-weight:bold;">{rank_name}</div>
        <div style="font-size:0.9em; color:#333;">Domande Dominate: <b>{mastered_count}</b> / {next_target}</div>
    </div>
    """, unsafe_allow_html=True)

def draw_question_card(q_id, topic, subtopic, text):
    # Nota: lo stile .question-card è definito in load_css con !important
    st.markdown(f"""
    <div class="question-card">
        <div style="color:#666; font-size:0.85em; margin-bottom:5px; font-weight:bold;">{q_id} • {topic}</div>
        <div style="color:#444; font-size:0.95em; font-style:italic; margin-bottom:15px;">{subtopic}</div>
        <div style="font-size:1.4em; font-weight:700; color:#000; line-height:1.4;">{text}</div>
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

# --- FUNZIONE STATISTICHE BLINDATA ---
def draw_stats_dashboard_advanced(df_stats):
    st.markdown("## 📊 Il Tuo Libretto")
    
    if df_stats is None or df_stats.empty:
        st.info("Fai qualche quiz per vedere i dati.")
        return

    try:
        tot = df_stats['Totali'].sum() if 'Totali' in df_stats.columns else 0
        svolte = df_stats['Svolte'].sum() if 'Svolte' in df_stats.columns else 0
        giuste = df_stats['Giuste'].sum() if 'Giuste' in df_stats.columns else 0
        prec = (giuste / svolte * 100) if svolte > 0 else 0
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Avanzamento", f"{int(svolte/tot*100)}%", f"{svolte}/{tot}")
        c2.metric("Precisione", f"{prec:.0f}%")
        
        if 'Svolte' in df_stats.columns and '% Precisione' in df_stats.columns:
            df_active = df_stats[df_stats['Svolte'] > 0]
            if not df_active.empty:
                weakest = df_active.sort_values(by='% Precisione').iloc[0]
                c3.metric("Punto Debole", f"{weakest['% Precisione']:.0f}%", weakest['Argomento'])
    except Exception as e:
        st.error(f"Errore calcolo metriche: {e}")

    try:
        target_cols = ['% Precisione', '% Completamento']
        valid_cols = [c for c in target_cols if c in df_stats.columns]
        
        st.dataframe(
            df_stats.style.background_gradient(cmap="RdYlGn", subset=valid_cols),
            use_container_width=True,
            hide_index=True
        )
    except Exception:
        st.dataframe(df_stats, use_container_width=True, hide_index=True)