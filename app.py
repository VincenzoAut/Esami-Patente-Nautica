# FILE: app.py
# VERSION: v110.0 (FIX: Spaziatura Header & Cronometro Iframe Style)
# DATE: 2026-01-11

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import os
import time
import datetime
import random
import urllib.parse
from PIL import Image

# Import moduli
import database as db_engine
import logic as brain
import ui 

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Patente Nautica", page_icon="⚓", layout="wide")

# --- CSS PERSONALIZZATO ---
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    .stDeployButton {display:none;}
    
    .stProgress > div > div > div > div {
        background-image: linear-gradient(to right, #4caf50, #8bc34a);
    }
    
    .credits-box {
        font-size: 0.75em;
        color: #888;
        text-align: center;
        margin-top: 10px;
        padding-top: 10px;
        border-top: 1px solid #eee;
    }

    div.row-widget.stButton > button {
        font-weight: bold;
    }
    
    /* --- BARRA DI STATO (SPAZIATA CORRETTAMENTE) --- */
    .status-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 12px;
        padding: 8px 20px; 
        margin-top: 10px;    /* SPAZIO DAL TITOLO SOPRA */
        margin-bottom: 20px; /* SPAZIO DAL CONTENUTO SOTTO */
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .status-item {
        text-align: center;
        font-family: sans-serif;
        line-height: 1.1;
    }
    .status-label {
        font-size: 0.75em;
        color: #666;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .status-value {
        font-size: 1.2em;
        font-weight: 800;
        color: #333;
    }

    /* --- STILE PAGINA BENVENUTO --- */
    .login-warning {
        padding: 2rem;
        background-color: transparent;
        text-align: center;
        margin-top: 50px;
    }
    .welcome-title {
        font-size: 3.5rem; 
        font-weight: 800; 
        color: #003366;
        text-shadow: 2px 2px 4px rgba(255, 255, 255, 0.8); 
        margin-bottom: 20px;
    }
    .welcome-text {
        font-size: 1.5rem; 
        color: #333; 
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(255, 255, 255, 0.8);
        line-height: 1.8;
    }

    /* LINK GOOGLE */
    .google-link {
        text-align: right; 
        margin-top: 15px; 
        margin-bottom: 10px;
    }
    .google-link a {
        text-decoration: none; 
        color: #333; 
        background-color: #f8f9fa;
        border: 1px solid #ccc; 
        padding: 8px 15px; 
        border-radius: 20px; 
        font-weight: bold;
        font-size: 0.9em;
        transition: all 0.3s;
    }
    .google-link a:hover {
        background-color: #e3f2fd;
        border-color: #2196f3;
        color: #0d47a1;
    }
</style>
""", unsafe_allow_html=True)

# --- PERCORSI FILE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_QUIZ_BASE_P = os.path.join(BASE_DIR, "Quiz_Patente_Base_Finale_OK.parquet")
FILE_QUIZ_BASE_X = os.path.join(BASE_DIR, "Quiz_Patente_Base_Finale_OK.xlsx")
FILE_QUIZ_VELA_P = os.path.join(BASE_DIR, "Quiz_Patente_Vela_Finale_OK.parquet")
FILE_QUIZ_VELA_X = os.path.join(BASE_DIR, "Quiz_Patente_Vela_Finale_OK.xlsx")
FILE_RACCORDO_P = os.path.join(BASE_DIR, "Raccordoimmagini.parquet")
FILE_RACCORDO_X = os.path.join(BASE_DIR, "Raccordoimmagini.xlsx")
CARTELLA_IMMAGINI = os.path.join(BASE_DIR, "Immagini_Quiz")

# UI SETUP
ui.set_backgrounds(os.path.join(BASE_DIR, "background.jpg"), os.path.join(BASE_DIR, "background2.jpg"))
ui.load_css()

# --- GESTIONE STATO ---
if 'init' not in st.session_state:
    st.session_state.current_user = "Comandante"
    st.session_state.quiz_mode = "Quiz Base"
    st.session_state.exam_mode = False
    st.session_state.review_mode = False
    st.session_state.stats_mode = False
    st.session_state.score_ok = 0
    st.session_state.score_ko = 0
    st.session_state.exam_index = 0
    st.session_state.exam_questions = []
    st.session_state.current_row = None
    st.session_state.answered = False
    st.session_state.last_answer_correct = False 
    st.session_state.selected_option_index = -1 
    st.session_state.shuffled_options = []
    st.session_state.end_timestamp = 0 
    st.session_state.start_time = 0     
    st.session_state.exam_finished = False
    
    raw_hist = db_engine.fetch_user_history("Comandante")
    st.session_state.history = {str(k).replace('.0','').strip(): v for k, v in raw_hist.items()}
    st.session_state.init = True

# --- LOGICA CARICAMENTO ---
if hasattr(brain, 'smart_load_data'):
    def load_data(mode):
        if "Vela" in mode: return brain.smart_load_data(FILE_QUIZ_VELA_P, FILE_QUIZ_VELA_X)
        return brain.smart_load_data(FILE_QUIZ_BASE_P, FILE_QUIZ_BASE_X)
    
    def load_raccordo_map():
        df = brain.smart_load_data(FILE_RACCORDO_P, FILE_RACCORDO_X)
        if df.empty: return {}
        try:
            col_id = 'ID Progressivo' if 'ID Progressivo' in df.columns else ('Progressivo' if 'Progressivo' in df.columns else None)
            col_img = 'Immagine' if 'Immagine' in df.columns else None
            if col_id and col_img:
                return dict(zip(df[col_id].astype(str).str.replace(r'\.0$', '', regex=True).str.strip(), df[col_img].astype(str).str.strip()))
        except: pass
        return {}
else:
    def load_data(mode):
        path = FILE_QUIZ_VELA_X if "Vela" in mode else FILE_QUIZ_BASE_X
        if os.path.exists(path): return pd.read_excel(path).fillna("").astype(str)
        return pd.DataFrame()
    def load_raccordo_map(): return {}

def get_image_path_for_question(question_id):
    if not question_id: return None
    raccordo_map = load_raccordo_map()
    clean_id = str(question_id).replace('.0','').strip()
    img_name = raccordo_map.get(clean_id)
    if not img_name: return None 
    target_path = os.path.join(CARTELLA_IMMAGINI, img_name)
    if os.path.exists(target_path): return target_path
    name_no_ext = os.path.splitext(img_name)[0].lower()
    for f in os.listdir(CARTELLA_IMMAGINI):
        if os.path.splitext(f)[0].lower() == name_no_ext: return os.path.join(CARTELLA_IMMAGINI, f)
    return None

# --- FUNZIONI QUIZ ---
def get_user_rank(mastered_count):
    if mastered_count < 100: return "🧹 Mozzo", 100
    if mastered_count < 300: return "⚓ Marinaio", 300
    if mastered_count < 500: return "🧭 Nostromo", 500
    if mastered_count < 700: return "🛳️ Comandante", 700
    return "🐺 Lupo di Mare", 1000

def finalize_exam(): st.session_state.exam_finished = True

def check_time_limit():
    if st.session_state.exam_mode and st.session_state.end_timestamp > 0:
        if time.time() > (st.session_state.end_timestamp + 2): finalize_exam(); return False
    return True

def reset_game(exam=False, review=False, stats=False):
    st.session_state.exam_mode = exam
    st.session_state.review_mode = review
    st.session_state.stats_mode = stats
    st.session_state.score_ok = 0
    st.session_state.score_ko = 0
    st.session_state.exam_index = 0
    st.session_state.answered = False
    st.session_state.exam_finished = False
    st.session_state.exam_questions = [] 
    st.session_state.start_time = time.time()
    
    duration = 0
    if exam:
        if "Vela" in st.session_state.quiz_mode: duration = 15 * 60 
        else: duration = 30 * 60 
        st.session_state.end_timestamp = st.session_state.start_time + duration
    else: 
        st.session_state.end_timestamp = 0

    db = load_data(st.session_state.quiz_mode)
    if db.empty: st.error("Database vuoto o non trovato."); return

    if not stats:
        if review:
            subset = brain.get_next_session_questions(db, st.session_state.history, mode="Ripasso")
            if len(subset) == 0: st.success("🎉 Nessun errore da ripassare!"); st.session_state.review_mode = False; return
            st.session_state.exam_questions = subset.to_dict('records'); load_question()
        elif exam:
            if "Vela" in st.session_state.quiz_mode: 
                st.session_state.exam_questions = db.sample(min(5, len(db))).to_dict('records')
            else: 
                st.session_state.exam_questions = brain.get_balanced_exam_questions(db).to_dict('records')
            load_question()
        else:
            subset = brain.get_next_session_questions(db, st.session_state.history, mode="Allenamento")
            st.session_state.exam_questions = subset.to_dict('records'); load_question()

def load_question():
    if st.session_state.exam_questions and st.session_state.exam_index < len(st.session_state.exam_questions):
        st.session_state.current_row = st.session_state.exam_questions[st.session_state.exam_index]
        prepare_options()
    else: finalize_exam()

def prepare_options():
    row = st.session_state.current_row
    if row is not None:
        if "Vela" in st.session_state.quiz_mode:
            raw_ans = str(row.get('Risposta Esatta', '')).strip().upper()
            is_vero = (raw_ans == 'A' or raw_ans == 'V' or raw_ans == 'VERO' or raw_ans == 'TRUE')
            st.session_state.shuffled_options = [{'txt': 'VERO', 'ok': is_vero}, {'txt': 'FALSO', 'ok': not is_vero}]
        else:
            corretta = str(row.get('Risposta Esatta','')).strip().upper()
            opts = [{'txt': row.get('Risposta A'), 'ok': corretta=='A'},
                    {'txt': row.get('Risposta B'), 'ok': corretta=='B'},
                    {'txt': row.get('Risposta C'), 'ok': corretta=='C'}]
            st.session_state.shuffled_options = [o for o in opts if pd.notna(o['txt']) and str(o['txt']).strip() != '']
            random.shuffle(st.session_state.shuffled_options)

def answer(is_correct, selected_idx):
    if not check_time_limit(): return 
    if not st.session_state.answered:
        st.session_state.answered = True
        st.session_state.last_answer_correct = is_correct
        st.session_state.selected_option_index = selected_idx
        
        id_dom = str(st.session_state.current_row.get('ID Progressivo')).strip()
        item_data = st.session_state.history.get(id_dom, {'score': 0, 'date': ''})
        new_score = item_data['score'] + 1 if (is_correct and item_data['score'] > 0) else (1 if is_correct else -1)
        st.session_state.history[id_dom] = {'score': new_score, 'date': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        db_engine.upsert_answer(st.session_state.current_user, id_dom, new_score)
        
        if is_correct: st.session_state.score_ok += 1
        else: st.session_state.score_ko += 1

def skip_current_question():
    if not check_time_limit(): return
    remaining = len(st.session_state.exam_questions) - st.session_state.exam_index
    if remaining <= 1: st.warning("⚠️ È l'ultima!"); return
    current_q = st.session_state.exam_questions.pop(st.session_state.exam_index)
    st.session_state.exam_questions.append(current_q); st.session_state.answered = False; st.toast("Saltata!"); load_question()

def next_question():
    if not check_time_limit(): return
    st.session_state.answered = False
    if st.session_state.exam_index + 1 < len(st.session_state.exam_questions):
        st.session_state.exam_index += 1; load_question()
    else: finalize_exam()

# --- SIDEBAR (LOGIN) ---
with st.sidebar:
    st.title("⚓ Patente Nautica")
    
    if st.session_state.current_user == "Comandante":
        st.markdown("### 🔑 Accesso Rapido")
        lista_utenti = db_engine.get_all_users()
        opzioni = ["➕ NUOVO ALLIEVO"] + [u.title() for u in lista_utenti]
        scelta = st.selectbox("Chi sei?", opzioni, label_visibility="collapsed")
        nome_da_usare = ""
        if scelta == "➕ NUOVO ALLIEVO":
            nome_da_usare = st.text_input("Scrivi il tuo nome:", placeholder="Nome Cognome...", key="new_user_input")
        else:
            nome_da_usare = scelta

        if st.button("ENTRA", type="primary", use_container_width=True):
            nome_clean = nome_da_usare.strip().lower()
            if len(nome_clean) < 3:
                st.toast("❌ Nome troppo corto!", icon="⚠️")
            else:
                st.session_state.current_user = nome_clean
                st.toast(f"Bentornato, {nome_clean.title()}!")
                raw_hist = db_engine.fetch_user_history(nome_clean)
                st.session_state.history = {str(k).replace('.0','').strip(): v for k, v in raw_hist.items()}
                st.session_state.exam_mode = False; st.session_state.review_mode = False; st.session_state.stats_mode = False
                st.rerun()
                
    else:
        st.success(f"👤 **{st.session_state.current_user.title()}**")
        if st.button("🚪 ESCI (Cambia Utente)", use_container_width=True):
            st.session_state.current_user = "Comandante"
            st.session_state.history = {} 
            st.rerun()

    if st.session_state.current_user != "Comandante":
        mastered = len([v for v in st.session_state.history.values() if v['score'] > 0])
        rank_n, rank_t = get_user_rank(mastered)
        ui.draw_rank_box(rank_n, mastered, rank_t)
        st.progress(min(mastered / rank_t, 1.0))
        
        st.write("---")
        st.markdown("**📚 Materia:**")
        mode = st.radio("Seleziona:", ["Quiz Base", "Quiz Vela"], label_visibility="collapsed")
        if mode != st.session_state.quiz_mode:
            st.session_state.quiz_mode = mode; st.session_state.current_row = None
            st.session_state.exam_questions = []; st.session_state.exam_mode = False; st.session_state.stats_mode = False; st.rerun()

        st.write("---")
        st.button("🎓 SIMULAZIONE ESAME", type="primary", use_container_width=True, on_click=reset_game, kwargs={'exam': True})
        st.button("♾️ ALLENAMENTO SMART", use_container_width=True, on_click=reset_game, kwargs={'exam': False})
        
        db = load_data(st.session_state.quiz_mode)
        if not db.empty:
            curr_ids = set(db['ID Progressivo'].astype(str))
            errs = 0
            for k, v in st.session_state.history.items():
                if v['score'] == -1 and str(k).replace('.0','').strip() in curr_ids: errs += 1
            if errs > 0: 
                st.warning(f"⚠️ **{errs} Errori da rivedere**")
                st.button("🔄 RIPASSA ERRORI", use_container_width=True, on_click=reset_game, kwargs={'review': True})
        
        st.button("📊 STATISTICHE", use_container_width=True, on_click=reset_game, kwargs={'stats': True})
    
    st.write("---")
    with st.expander("ℹ️ Info & Regole d'uso"):
        st.markdown("""
        **⚓ A cosa serve questa App?**
        Questa applicazione è uno strumento professionale progettato per portarti al conseguimento della **Patente Nautica**.

        ### 1. 🎓 SIMULAZIONE ESAME
        * **🅰️ QUIZ BASE:** 30 domande (30 min, max 4 errori).
        * **⛵ QUIZ VELA:** 5 domande (15 min, max 1 errore).

        ### 2. ♾️ ALLENAMENTO SMART
        Algoritmo SRS: Ripropone le domande che sbagli finché non le impari.
        """)
    
    if st.session_state.current_row is not None and st.session_state.current_user != "Comandante":
        st.write("---")
        with st.expander("🚩 Segnala Errore Quiz"):
            msg = st.text_area("Descrivi il problema:", height=80, key="sidebar_report")
            if st.button("Invia Segnalazione", key="sidebar_send"):
                if msg:
                    curr_id = st.session_state.current_row.get('ID Progressivo')
                    ok = db_engine.save_report(st.session_state.current_user, curr_id, msg)
                    if ok: st.success("Inviato!")
                    else: st.error("Errore.")
                else:
                    st.warning("Scrivi un messaggio.")

    st.markdown("""<div class='credits-box'><b>Developed by Vincenzo Autolitano</b><br>v110.0 • Powered by Gemini AI</div>""", unsafe_allow_html=True)


# --- GATEKEEPER ---
if st.session_state.current_user == "Comandante":
    st.markdown("""
    <div class='login-warning'>
        <div class='welcome-title'>⚓ BENVENUTO A BORDO!</div>
        <div class='welcome-text'>
            <p>Per iniziare la navigazione:</p>
            <p>👈 <b>1. Vai nella barra laterale a sinistra</b></p>
            <p>👈 <b>2. Seleziona il tuo nome e premi ENTRA</b></p>
            <p>📝 <b>3. Se sei un nuovo allievo, inserisci il tuo nome</b></p>
            <p style="margin-top:20px; color:#2e7d32;">🌊 <b>4. Buon vento!</b></p>
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- APP PRINCIPALE ---
icon = {'Vela': '⛵', 'Base': '🛥️'}.get(st.session_state.quiz_mode, '⚓')

if st.session_state.stats_mode:
    full_db = load_data(st.session_state.quiz_mode)
    stats_df = brain.calculate_topic_stats(full_db, st.session_state.history)
    ui.draw_stats_dashboard_advanced(stats_df)
    if st.button("⬅️ Torna ai Quiz", type="primary"): st.session_state.stats_mode = False; st.rerun()

else:
    # HEADER (TITOLO + TIMER)
    if st.session_state.exam_mode:
        c_head, c_time = st.columns([3, 1])
        with c_head: 
            # Titolo H3 pulito
            st.markdown(f"<h3 style='margin-top:0; margin-bottom:5px;'>🎓 {st.session_state.quiz_mode} - SIMULAZIONE ESAME</h3>", unsafe_allow_html=True)
        with c_time:
            if st.session_state.end_timestamp > 0 and not st.session_state.exam_finished:
                end_js = int(st.session_state.end_timestamp * 1000)
                
                # --- FIX CRONOMETRO: CSS INLINE PERCHE' DENTRO IFRAME ---
                # Il bordo e lo stile ora sono definiti DENTRO l'HTML del componente
                timer_html = f"""
                <style>
                    body {{ margin: 0; padding: 0; display:flex; justify-content:center; }}
                    .timer-box {{
                        font-family: monospace; 
                        display: flex; 
                        justify-content: center; 
                        align-items: center; 
                        background: #fffbf0; 
                        padding: 8px 15px; 
                        border-radius: 8px; 
                        border: 2px solid #ff9800; 
                        width: 95%;
                        box-sizing: border-box;
                        white-space: nowrap;
                        color: #d32f2f;
                        font-weight: bold;
                        font-size: 1.2em;
                    }}
                </style>
                <div class="timer-box">
                    <span style="margin-right:8px; font-size:0.9em; color:#555;">⏱️</span>
                    <span id="cnt">--:--</span>
                </div>
                <script>
                setInterval(function(){{
                    var dist={end_js}-new Date().getTime(); 
                    if(dist<0) document.getElementById("cnt").innerHTML="SCADUTO"; 
                    else {{ 
                        var m=Math.floor((dist%(1000*60*60))/(1000*60)); 
                        var s=Math.floor((dist%(1000*60))/1000); 
                        document.getElementById("cnt").innerHTML=(m<10?"0"+m:m)+":"+(s<10?"0"+s:s); 
                    }} 
                }}, 1000);
                </script>
                """
                components.html(timer_html, height=70)
                if time.time() > (st.session_state.end_timestamp + 2): finalize_exam(); st.rerun()
    else:
        t_suffix = "Ripasso" if st.session_state.review_mode else "Allenamento"
        st.markdown(f"## {icon} {st.session_state.quiz_mode} - *{t_suffix}*")
    
    # METRICHE (BARRA CON SPAZIO AGGIUNTIVO)
    if not st.session_state.exam_finished:
        done = st.session_state.score_ok + st.session_state.score_ko
        tot = len(st.session_state.exam_questions)
        
        st.markdown(f"""
        <div class="status-bar">
            <div class="status-item">
                <div class="status-label">Fatte</div>
                <div class="status-value">{done}/{tot}</div>
            </div>
            <div class="status-item">
                <div class="status-label">Esatte</div>
                <div class="status-value" style="color:#2e7d32;">{st.session_state.score_ok}</div>
            </div>
            <div class="status-item">
                <div class="status-label">Errori</div>
                <div class="status-value" style="color:#c62828;">{st.session_state.score_ko}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if tot > 0: st.progress(done/tot)
    
    # SCHERMATA FINE ESAME
    if st.session_state.exam_finished:
        st.markdown('<div class="question-card">', unsafe_allow_html=True)
        limit = 4 if "Base" in st.session_state.quiz_mode else 1
        if st.session_state.exam_mode:
            if st.session_state.score_ko <= limit: 
                st.balloons()
                st.markdown(f"<div class='exam-pass'><h1>🎉 SUPERATO!</h1><p>Errori commessi: {st.session_state.score_ko} (Max: {limit})</p></div>", unsafe_allow_html=True)
            else: 
                st.markdown(f"<div class='exam-fail'><h1>🚫 NON SUPERATO</h1><p>Errori commessi: {st.session_state.score_ko} (Max consentiti: {limit})</p></div>", unsafe_allow_html=True)
        else: st.markdown("<div class='review-end'><h1>✅ Fine Sessione</h1></div>", unsafe_allow_html=True)
        st.button("🔄 NUOVA SESSIONE", type="primary", on_click=reset_game, kwargs={'exam': st.session_state.exam_mode})
        st.markdown('</div>', unsafe_allow_html=True)

    # DOMANDA E RISPOSTE
    elif st.session_state.current_row is not None:
        row = st.session_state.current_row
        c1, c2 = st.columns([1, 2])
        with c1:
            path = get_image_path_for_question(row.get('ID Progressivo'))
            if path: st.image(Image.open(path))
        with c2:
            ui.draw_question_card(row.get('ID Progressivo'), row.get('Argomento'), row.get('Voce', ''), row.get('Domanda'))
            
            if st.session_state.answered:
                # MOSTRA RISULTATO
                for i, opt in enumerate(st.session_state.shuffled_options):
                    is_selected_by_user = (i == st.session_state.selected_option_index)
                    ui.draw_result_option(opt['txt'], opt['ok'], is_selected_by_user, st.session_state.last_answer_correct)
                
                # --- LINK GOOGLE ---
                q_text = row.get('Domanda', '')
                short_q = (q_text[:75] + '..') if len(q_text) > 75 else q_text
                encoded_query = urllib.parse.quote(f"Patente Nautica {short_q}")
                
                st.markdown(f"""
                <div class='google-link'>
                    <a href="https://www.google.com/search?q={encoded_query}" target="_blank">
                        🔍 Approfondisci su Google
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button("PROSSIMA DOMANDA ➡", type="primary", use_container_width=True): 
                    next_question(); st.rerun()

            else:
                # MOSTRA OPZIONI
                for i, opt in enumerate(st.session_state.shuffled_options):
                    btn_label = opt['txt']
                    if "Vela" in st.session_state.quiz_mode: btn_label = f"⚪ {opt['txt']}"
                    if st.button(btn_label, key=f"btn_{i}", use_container_width=True):
                        answer(opt['ok'], i); st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
                c_skip, c_idk = st.columns(2)
                with c_skip:
                    if st.session_state.exam_mode:
                        if st.button("⏭️ SALTA", use_container_width=True): skip_current_question(); st.rerun()
                with c_idk:
                    if st.button("🚩 Non la so!", use_container_width=True): answer(False, -1); st.rerun()
    
    if st.session_state.current_row is None: reset_game(False); st.rerun()