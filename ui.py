# FILE: ui.py
# VERSION: v102.3 (Fix Missing rank box + Compass Position)
# DATE: 2026-01-11

import streamlit as st
import base64
import os

def get_base64_of_bin_file(bin_file):
    """Converte un file binario (immagine) in base64 per l'uso nel CSS."""
    try:
        with open(bin_file, 'rb') as f: data = f.read()
        return base64.b64encode(data).decode()
    except FileNotFoundError: return None

def load_css():
    """Carica gli stili base dell'interfaccia (nasconde menu, footer, ecc)."""
    st.markdown("""
    <style>
        /* Nascondi elementi standard di Streamlit */
        #MainMenu {visibility: hidden;}
        header {visibility: hidden;}
        footer {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Stile Barra di Progresso */
        .stProgress > div > div > div > div {
            background-image: linear-gradient(to right, #4caf50, #8bc34a);
        }
        
        /* Stile Box Crediti */
        .credits-box {
            font-size: 0.75em;
            color: #888;
            text-align: center;
            margin-top: 10px;
            padding-top: 10px;
            border-top: 1px solid #eee;
        }

        /* Stile Bottoni */
        div.row-widget.stButton > button {
            font-weight: bold;
        }
    </style>
    """, unsafe_allow_html=True)

def set_backgrounds(main_bg, sidebar_bg):
    """Imposta gli sfondi per l'app principale e la sidebar."""
    
    # 1. SFONDO PRINCIPALE (Bussola in basso)
    if os.path.exists(main_bg):
        bin_str = get_base64_of_bin_file(main_bg)
        st.markdown(f"""
        <style>
            .stApp {{ 
                background-image: url(data:image/jpg;base64,{bin_str}) !important; 
                background-size: cover !important; 
                /* ANCORAGGIO IN BASSO PER LA BUSSOLA */
                background-position: bottom center !important; 
                background-repeat: no-repeat !important;
                background-attachment: fixed !important; 
            }}
        </style>
        """, unsafe_allow_html=True)
        
    # 2. SFONDO SIDEBAR
    if os.path.exists(sidebar_bg):
        bin_str_side = get_base64_of_bin_file(sidebar_bg)
        st.markdown(f"""
        <style>
            section[data-testid="stSidebar"] {{ 
                background-image: url(data:image/jpg;base64,{bin_str_side}) !important; 
                background-size: cover !important; 
                background-position: center center !important;
            }} 
            section[data-testid="stSidebar"] > div:first-child {{ 
                background-color: rgba(255, 255, 255, 0.1); 
            }}
        </style>
        """, unsafe_allow_html=True)

def draw_rank_box(rank_name, mastered_count, next_threshold):
    """Visualizza il grado attuale dell'utente nella sidebar."""
    
    # Calcola il testo per il prossimo livello
    next_text = ""
    try:
        if isinstance(next_threshold, (int, float)):
            left = int(next_threshold) - int(mastered_count)
            if left > 0:
                next_text = f"Mancano {left} giuste al prossimo grado"
            else:
                next_text = "Massimo grado raggiunto!"
        else:
            next_text = str(next_threshold)
    except:
        next_text = ""

    st.markdown(f"""
    <div style="
        background: rgba(0, 0, 0, 0.6);
        border-radius: 10px;
        padding: 15px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    ">
        <div style="font-size: 0.8em; color: #ccc; text-transform: uppercase; letter-spacing: 1px;">Grado Attuale</div>
        <div style="font-size: 1.3em; font-weight: bold; color: #FFD700; margin: 5px 0;">⚓ {rank_name}</div>
        <div style="font-size: 0.75em; color: #eee; margin-top: 5px;">{next_text}</div>
    </div>
    """, unsafe_allow_html=True)

def draw_response_feedback(is_correct, text, is_selected=True):
    """Disegna il box colorato con il feedback della risposta."""
    st.markdown("""
    <style>
    .res-box {
        padding: 15px;
        border-radius: 10px;
        margin-bottom: 10px;
        font-weight: bold;
        color: white;
        display: flex;
        align-items: center;
        font-family: sans-serif;
    }
    .res-correct { background-color: rgba(76, 175, 80, 0.9); border: 2px solid #2E7D32; }
    .res-wrong { background-color: rgba(244, 67, 54, 0.9); border: 2px solid #C62828; }
    .res-neutral { background-color: rgba(158, 158, 158, 0.8); border: 2px solid #616161; color: #EEE; }
    </style>
    """, unsafe_allow_html=True)

    style = ""
    icon = ""

    if is_selected:
        if is_correct:
            style = "res-correct"
            icon = "✅"
        else:
            style = "res-wrong"
            icon = "❌"
    else:
        if is_correct: 
            style = "res-neutral"
            icon = "👉" 
        else:
            style = "res-neutral"
            icon = "⚪"
        
    st.markdown(f'<div class="res-box {style}">{icon}&nbsp;&nbsp;{text}</div>', unsafe_allow_html=True)

def draw_stats_dashboard_advanced(df_stats):
    """Visualizza le metriche dell'utente."""
    st.markdown("## 📊 Il Tuo Libretto")
    
    if df_stats is None or df_stats.empty:
        st.info("Fai qualche quiz per vedere i dati.")
        return

    tot = df_stats['Totali'].sum()
    svolte = df_stats['Svolte'].sum()
    giuste = df_stats['Giuste'].sum()
    
    prec = (giuste / svolte * 100) if svolte > 0 else 0
    avanzamento = int(svolte / tot * 100) if tot > 0 else 0
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Avanzamento", f"{avanzamento}%", f"{svolte}/{tot}")
    c2.metric("Precisione", f"{prec:.0f}%")
    
    df_active = df_stats[df_stats['Svolte'] > 0].copy()
    
    if not df_active.empty and '% Precisione' in df_active.columns:
        weakest = df_active.sort_values(by='% Precisione', ascending=True).iloc[0]
        arg_name = weakest['Argomento']
        if len(arg_name) > 15: arg_name = arg_name[:12] + "..."
        c3.metric("Da Ripassare", arg_name, f"{weakest['% Precisione']:.0f}%")
    else:
        c3.metric("Stato", "Ottimo!", "Continua così")