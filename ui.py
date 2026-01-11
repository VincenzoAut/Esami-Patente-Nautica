# FILE: ui.py
# VERSION: v54.0 (Mobile UX & Visual Feedback)
# DATE: 2026-01-10 21:45

import streamlit as st
import base64
import os

def get_base64_of_bin_file(bin_file):
    try:
        with open(bin_file, 'rb') as f: data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError: return None

def set_backgrounds(main_bg, sidebar_bg):
    if os.path.exists(main_bg):
        bin_str = get_base64_of_bin_file(main_bg)
        st.markdown(f"""<style>.stApp {{ background-image: url(data:image/jpg;base64,{bin_str}) !important; background-size: cover !important; background-attachment: fixed !important; }}</style>""", unsafe_allow_html=True)
    if os.path.exists(sidebar_bg):
        bin_str_side = get_base64_of_bin_file(sidebar_bg)
        st.markdown(f"""<style>section[data-testid="stSidebar"] {{ background-image: url(data:image/jpg;base64,{bin_str_side}) !important; background-size: cover !important; }} section[data-testid="stSidebar"] > div:first-child {{ background-color: rgba(255, 255, 255, 0.5) !important; }}</style>""", unsafe_allow_html=True)

def load_css():
    st.markdown("""
    <style>
        .block-container { padding-top: 1rem !important; }
        
        /* TESTI PIÙ LEGGIBILI */
        .stRadio label, .stMarkdown p, .stText, h1, h2, h3, li { 
            color: #000000 !important; 
            font-weight: 500; 
            font-size: 1.1rem !important;
        }

        /* BOTTONI "POLLICIONE" (MOBILE FRIENDLY) */
        div.stButton > button { 
            width: 100%;             /* Occupa tutta la larghezza */
            min-height: 60px;        /* Molto più alti */
            font-size: 18px !important; /* Testo più grande */
            border-radius: 12px; 
            margin-bottom: 8px; 
            background-color: #ffffff !important; 
            border: 2px solid #ced4da !important; 
            color: #212529 !important; 
            box-shadow: 0 4px 6px rgba(0,0,0,0.1); 
            transition: all 0.2s;
        }
        div.stButton > button:active { transform: scale(0.98); }
        
        /* Bottoni speciali (Primary) */
        div.stButton > button[kind="primary"] { 
            background-color: #0d6efd !important; 
            color: white !important; 
            border: none !important; 
            font-weight: bold !important; 
        }

        /* CARD DOMANDA */
        .question-box { 
            background-color: rgba(255, 255, 255, 0.95); 
            padding: 25px; 
            border-radius: 15px; 
            border-left: 8px solid #1565c0; 
            margin-bottom: 25px; 
            box-shadow: 0 8px 16px rgba(0,0,0,0.15); 
        }
        .question-header { 
            display: flex; justify-content: space-between; margin-bottom: 15px; 
            border-bottom: 1px solid #ddd; padding-bottom: 5px; 
            font-size: 0.9rem; color: #666;
        }
        .question-id { font-weight: 900; color: #1565c0; }
        .question-text { font-size: 22px; line-height: 1.4; font-weight: 700; color: #2c3e50; }

        /* DASHBOARD */
        .rank-box { background: linear-gradient(135deg, #0061f2 0%, #00c6f7 100%); padding: 15px; border-radius: 8px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.2); }
        .metric-container { display: flex; justify-content: space-between; background-color: rgba(255,255,255,0.9); padding: 10px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); margin-bottom: 15px; }
        .metric-box { text-align: center; width: 33%; font-weight: bold; }
        .footer-sidebar { font-size: 11px; text-align: center; margin-top: 30px; opacity: 0.7; }
        
        /* RISULTATI */
        .res-box { padding: 15px; border-radius: 10px; margin-bottom: 8px; font-weight: 600; font-size: 18px; border: 1px solid rgba(0,0,0,0.1); }
        .res-correct { background-color: #d1e7dd; color: #0f5132; border-color: #badbcc; }
        .res-wrong { background-color: #f8d7da; color: #842029; border-color: #f5c2c7; text-decoration: line-through; opacity: 0.8; }
        .res-neutral { background-color: #f8f9fa; color: #6c757d; border-color: #dee2e6; opacity: 0.6; }
        
    </style>
    """, unsafe_allow_html=True)

def draw_question_card(id_prog, argomento, voce, testo):
    st.markdown(f'<div class="question-box"><div class="question-header"><span class="question-id">#{id_prog}</span><span>{argomento}</span></div><div class="question-text">{testo}</div></div>', unsafe_allow_html=True)

def draw_rank_box(rank_name, current, target):
    st.markdown(f'<div class="rank-box"><div class="rank-title">GRADO</div><div class="rank-name">{rank_name}</div><div>{current} / {target} XP</div></div>', unsafe_allow_html=True)

# NUOVA FUNZIONE PER I RISULTATI COLORATI
def draw_result_option(text, is_correct, user_selected_this, user_answered_correctly):
    """Disegna il box colorato dopo la risposta."""
    if is_correct:
        # È la risposta giusta: SEMPRE VERDE
        style = "res-correct"
        icon = "✅"
    elif user_selected_this and not is_correct:
        # L'utente ha cliccato questa ed era sbagliata: ROSSA
        style = "res-wrong"
        icon = "❌"
    else:
        # Risposta sbagliata non cliccata: GRIGIA/NEUTRA
        style = "res-neutral"
        icon = "⚪"
        
    st.markdown(f'<div class="res-box {style}">{icon} {text}</div>', unsafe_allow_html=True)

def draw_stats_dashboard_advanced(df_stats):
    st.markdown("## 📊 Il Tuo Libretto")
    if df_stats.empty:
        st.info("Fai qualche quiz per vedere i dati.")
        return

    tot = df_stats['Totali'].sum()
    svolte = df_stats['Svolte'].sum()
    giuste = df_stats['Giuste'].sum()
    prec = (giuste / svolte * 100) if svolte > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Avanzamento", f"{int(svolte/tot*100)}%", f"{svolte}/{tot}")
    c2.metric("Precisione", f"{prec:.0f}%")
    
    # Punto debole
    df_active = df_stats[df_stats['Svolte'] > 0]
    if not df_active.empty:
        weakest = df_active.sort_values(by='% Precisione').iloc[0]
        c3.metric("Ripassa:", weakest['Argomento'], f"{weakest['% Precisione']}%", delta_color="inverse")
    else: c3.metric("Ripassa:", "-")

    st.markdown("---")
    st.subheader("📝 Dettaglio per Materia")
    st.dataframe(
        df_stats[['Argomento', 'Svolte', 'Giuste', 'Sbagliate']],
        hide_index=True,
        use_container_width=True,
        column_config={
            "Giuste": st.column_config.NumberColumn("✅", format="%d"),
            "Sbagliate": st.column_config.NumberColumn("❌", format="%d")
        }
    )