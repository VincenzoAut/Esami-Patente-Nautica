# FILE: app.py
# VERSION: v119.0 (UX: Instant Start on Topic Selection)
# DATE: 2026-01-12

import streamlit as st
import pandas as pd
import os
import time
import datetime
import random
import urllib.parse
from PIL import Image

# Import moduli personalizzati
import database as db_engine
import logic as brain
import ui 
import admin
import students_engine

PRIVACY_TEXT = ("**Titolare del trattamento:** Vincenzo Autolitano - vincenzo.autolitano@gmail.com. ""**Finalita:** gestione didattica degli allievi (accesso all app, storico delle risposte, statistiche di apprendimento). ""**Dati trattati:** nome, indirizzo email, risposte ai quiz e relativi punteggi. ""**Base giuridica:** consenso dell interessato. ""**Conservazione:** 24 mesi dall ultima attivita, poi cancellazione. ""**Comunicazione:** nessun dato e condiviso con terzi; il database e ospitato su Supabase. ""**Diritti:** accesso, rettifica, cancellazione e portabilita scrivendo al titolare.")

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Patente Nautica", page_icon="⚓", layout="wide", initial_sidebar_state="expanded")

# --- PERCORSI FILE ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FILE_QUIZ_BASE_P = os.path.join(BASE_DIR, "Quiz_Patente_Base_Finale_OK.parquet")
FILE_QUIZ_BASE_X = os.path.join(BASE_DIR, "Quiz_Patente_Base_Finale_OK.xlsx")
FILE_QUIZ_VELA_P = os.path.join(BASE_DIR, "Quiz_Patente_Vela_Finale_OK.parquet")
FILE_QUIZ_VELA_X = os.path.join(BASE_DIR, "Quiz_Patente_Vela_Finale_OK.xlsx")
FILE_RACCORDO_P = os.path.join(BASE_DIR, "Raccordoimmagini.parquet")
FILE_RACCORDO_X = os.path.join(BASE_DIR, "Raccordoimmagini.xlsx")
CARTELLA_IMMAGINI = os.path.join(BASE_DIR, "Immagini_Quiz")
CSS_FILE = os.path.join(BASE_DIR, "style.css")

# --- FUNZIONE CARICAMENTO CSS ---
def local_css(file_name):
    if os.path.exists(file_name):
        with open(file_name) as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# UI SETUP
local_css(CSS_FILE)
ui.set_backgrounds(os.path.join(BASE_DIR, "background.jpg"), os.path.join(BASE_DIR, "background2.jpg"))
ui.load_css()

# --- GESTIONE STATO ---
brain.initialize_app_state()

# --- PANNELLO ISTRUTTORE ---
if st.session_state.get("admin_mode", False):
    admin.render_admin_dashboard()
    st.stop()

# --- LOGICA CARICAMENTO DATI ---
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

# --- FUNZIONI QUIZ E RESET ---
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

# --- NUOVA CALLBACK: AVVIO DIRETTO AL CAMBIO FILTRO ---
def start_filtered_training():
    """Avvia direttamente l'allenamento quando cambia il filtro nel menu a tendina."""
    # Recupera il valore appena selezionato dallo stato
    selected = st.session_state.topic_filter
    # Avvia il reset del gioco passando il topic
    reset_game(exam=False, topic=selected)

def reset_game(exam=False, review=False, stats=False, topic=None):
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
    st.session_state.total_pending_errors = 0 
    
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
            curr_ids = set(db['ID Progressivo'].astype(str))
            total_errs = 0
            for k, v in st.session_state.history.items():
                if v['score'] == -1 and str(k).replace('.0','').strip() in curr_ids:
                    total_errs += 1
            st.session_state.total_pending_errors = total_errs

            subset = brain.get_next_session_questions(db, st.session_state.history, mode="Ripasso")
            if len(subset) == 0: 
                st.success("🎉 Nessun errore da ripassare!"); 
                st.session_state.review_mode = False; 
                return
            st.session_state.exam_questions = subset.to_dict('records'); load_question()
        
        elif exam:
            if "Vela" in st.session_state.quiz_mode: 
                st.session_state.exam_questions = db.sample(min(5, len(db))).to_dict('records')
            else: 
                st.session_state.exam_questions = brain.get_balanced_exam_questions(db).to_dict('records')
            load_question()
        else:
            # ALLENAMENTO CON FILTRO
            if topic and topic != "Tutti gli argomenti" and "Argomento" in db.columns:
                db = db[db['Argomento'] == topic]
                if db.empty:
                    st.warning(f"Nessuna domanda trovata per l'argomento: {topic}")
                    return

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

# --- SIDEBAR (LOGIN & MENU) ---
with st.sidebar:
    st.title("⚓ Patente Nautica")
    
    if st.session_state.current_user == "Comandante":
        st.markdown("### 🔑 Accesso")
        try:
            _admin_pin = str(st.secrets["app"]["admin_pin"])
        except Exception:
            _admin_pin = ""

        def _do_login(user_id):
            st.session_state.current_user = user_id
            raw_hist = db_engine.fetch_user_history(user_id)
            st.session_state.history = {str(k).replace(".0", "").strip(): v for k, v in raw_hist.items()}
            st.session_state.quiz_mode = "Quiz Base"
            st.session_state.exam_mode = True
            st.session_state.review_mode = False
            st.session_state.stats_mode = False
            reset_game(exam=True)
            st.rerun()

        _db_students = students_engine.list_students()
        _secrets_students = {}
        try:
            for _k, _v in st.secrets["students"].items():
                _secrets_students[str(_k).lower()] = str(_v.get("pin", "")) if hasattr(_v, "get") else str(_v)
        except Exception:
            _secrets_students = {}

        if _db_students:
            _labels = [r["display_name"] for r in _db_students]
            _ids = {r["display_name"]: r["user_id"] for r in _db_students}
            scelta = st.selectbox("Chi sei?", _labels, label_visibility="collapsed")
            pin_ins = st.text_input("PIN personale", type="password", placeholder="4 cifre", key="pin_studente")
            _consenso = st.checkbox("Ho letto e accetto l informativa privacy", key="consenso_login")
            if st.button("ENTRA", type="primary", width="stretch"):
                res = students_engine.login_student(_ids[scelta], pin_ins.strip()) if pin_ins.strip() else None
                if not _consenso:
                    st.error("Spunta l informativa privacy per entrare.")
                elif res and res.get("ok"):
                    students_engine.record_consent(str(res.get("user_id") or _ids[scelta]), pin_ins.strip())
                    _do_login(str(res.get("user_id") or _ids[scelta]))
                elif res and res.get("locked"):
                    _min = max(1, int(res.get("retry_after", 300)) // 60 + 1)
                    st.error(f"Troppi tentativi. Riprova tra {_min} minuti.")
                else:
                    st.error("PIN errato.")
        elif _secrets_students:
            _nomi = sorted(_secrets_students.keys())
            scelta = st.selectbox("Chi sei?", [n.title() for n in _nomi], label_visibility="collapsed")
            pin_ins = st.text_input("PIN personale", type="password", placeholder="4 cifre", key="pin_studente")
            if st.button("ENTRA", type="primary", width="stretch"):
                nome_clean = scelta.strip().lower()
                if pin_ins.strip() and pin_ins.strip() == _secrets_students.get(nome_clean, ""):
                    _do_login(nome_clean)
                else:
                    st.error("PIN errato.")
        else:
            st.warning("Nessun allievo configurato.")

        with st.expander("🔒 Informativa privacy"):
            st.markdown(PRIVACY_TEXT)

        with st.expander("✉️ Non sei in elenco? Richiedi accesso"):
            _req_nome = st.text_input("Nome e cognome", key="req_nome")
            _req_mail = st.text_input("Email", key="req_mail")
            _req_consenso = st.checkbox("Ho letto e accetto l informativa privacy", key="req_consent")
            if st.button("Invia richiesta", key="req_btn"):
                if not _req_consenso:
                    st.error("Devi accettare l informativa privacy.")
                elif len(_req_nome.strip()) >= 3 and "@" in _req_mail:
                    _res = students_engine.request_access(_req_nome.strip(), _req_mail.strip(), True)
                    if _res.get("ok"):
                        _canali = students_engine.notify_access(_req_nome.strip(), _req_mail.strip())
                        _extra = (" Avviso inviato via " + ", ".join(_canali) + ".") if _canali else ""
                        st.success("Richiesta inviata." + _extra)
                    else:
                        st.error(_res.get("error", "Errore invio richiesta."))
                else:
                    st.error("Inserisci nome ed email validi.")

        with st.expander("🔐 Area istruttore"):
            _ap = st.text_input("PIN istruttore", type="password", key="pin_admin")
            if st.button("Apri pannello", key="btn_admin"):
                try:
                    _sb = db_engine.init_connection()
                    _res = _sb.rpc("admin_login", {"p_pin": _ap.strip()}).execute().data if _sb else {"ok": False}
                except Exception as _e:
                    _res = {"ok": False, "error": str(_e)}
                if _res.get("ok"):
                    st.session_state.admin_pin_value = _ap.strip()
                    st.session_state.admin_mode = True
                    st.rerun()
                elif _res.get("locked"):
                    _min = max(1, int(_res.get("retry_after", 300)) // 60 + 1)
                    st.error(f"Troppi tentativi. Riprova tra {_min} minuti.")
                else:
                    st.error("PIN errato.")

    else:
        st.success(f"👤 **{st.session_state.current_user.title()}**")
        if st.button("🚪 ESCI (Cambia Utente)", width="stretch"):
            st.session_state.current_user = "Comandante"
            st.session_state.history = {} 
            st.rerun()
        with st.expander("🔑 Cambia il mio PIN"):
            _np = st.text_input("Nuovo PIN", type="password", key="cambia_pin_nuovo")
            _np2 = st.text_input("Conferma nuovo PIN", type="password", key="cambia_pin_conf")
            if st.button("Aggiorna PIN", key="btn_cambia_pin"):
                _apin2 = ""
                try:
                    _apin2 = str(st.secrets["app"]["admin_pin"])
                except Exception:
                    _apin2 = ""
                if len(_np.strip()) < 4:
                    st.error("Il PIN deve avere almeno 4 caratteri.")
                elif _np.strip() != _np2.strip():
                    st.error("I due PIN non coincidono.")
                elif not _apin2:
                    st.error("Configurazione admin mancante.")
                else:
                    _r = students_engine.admin_reset_pin(st.session_state.current_user, _np.strip(), _apin2)
                    if _r.get("ok"):
                        st.success("PIN aggiornato.")
                    else:
                        st.error(_r.get("error", "Errore"))

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
        
        # --- SELETTORE ARGOMENTO (VISIBILE SOLO IN ALLENAMENTO BASE) ---
        # Nascondiamo se stiamo facendo l'esame (exam_mode=True)
        selected_topic = "Tutti gli argomenti" 
        
        if "Base" in st.session_state.quiz_mode and not st.session_state.exam_mode:
            db_temp = load_data("Quiz Base")
            if not db_temp.empty and 'Argomento' in db_temp.columns:
                topics_list = sorted(db_temp['Argomento'].unique().astype(str))
                options = ["Tutti gli argomenti"] + topics_list
                
                if 'topic_filter' not in st.session_state:
                    st.session_state.topic_filter = "Tutti gli argomenti"
                
                # QUI C'È LA MAGIA: on_change=start_filtered_training
                # Appena cambi, parte il quiz su quell'argomento
                selected_topic = st.selectbox(
                    "🎯 Filtra Argomento:", 
                    options, 
                    key="topic_filter",
                    on_change=start_filtered_training 
                )
        
        st.button("🎓 SIMULAZIONE ESAME", type="primary", width="stretch", on_click=reset_game, kwargs={'exam': True})
        
        # Il pulsante rimane per chi vuole cliccare, ma il selectbox già avvia tutto.
        st.button("♾️ ALLENAMENTO SMART", width="stretch", on_click=reset_game, kwargs={'exam': False, 'topic': selected_topic})
        
        db = load_data(st.session_state.quiz_mode)
        if not db.empty:
            curr_ids = set(db['ID Progressivo'].astype(str))
            errs_count = 0
            for k, v in st.session_state.history.items():
                if v['score'] == -1 and str(k).replace('.0','').strip() in curr_ids: 
                    errs_count += 1
            
            if errs_count > 0: 
                st.warning(f"⚠️ **{errs_count} Errori in memoria**")
                if st.button("🔄 RIPASSA ERRORI", width="stretch"):
                    reset_game(review=True)
                    st.rerun()
            else:
                st.success("✅ Nessun errore in sospeso")
        
        st.button("📊 STATISTICHE", width="stretch", on_click=reset_game, kwargs={'stats': True})
    
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

    st.markdown("""<div class='credits-box'><b>Developed by Vincenzo Autolitano</b><br>v119.0 • Powered by Gemini AI</div>""", unsafe_allow_html=True)


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
            st.markdown(f"<h3 style='margin-top:0; margin-bottom:5px;'>🎓 {st.session_state.quiz_mode} - SIMULAZIONE ESAME</h3>", unsafe_allow_html=True)
        with c_time:
            if st.session_state.end_timestamp > 0 and not st.session_state.exam_finished:
                ui.display_exam_timer(st.session_state.end_timestamp)
                if time.time() > (st.session_state.end_timestamp + 2): finalize_exam(); st.rerun()
    else:
        t_suffix = "Ripasso" if st.session_state.review_mode else "Allenamento"
        st.markdown(f"## {icon} {st.session_state.quiz_mode} - *{t_suffix}*")
    
    # METRICHE E STATUS BAR
    if not st.session_state.exam_finished:
        done = st.session_state.score_ok + st.session_state.score_ko
        session_tot = len(st.session_state.exam_questions)
        
        label_tot = f"{done}/{session_tot}"
        if st.session_state.review_mode:
            label_tot = f"{done} / {st.session_state.total_pending_errors}"

        st.markdown(f"""
        <div class="status-bar">
            <div class="status-item">
                <div class="status-label">Avanzamento</div>
                <div class="status-value">{label_tot}</div>
            </div>
            <div class="status-item">
                <div class="status-label">Esatte</div>
                <div class="status-value" style="color:#2e7d32;">{st.session_state.score_ok}</div>
            </div>
            <div class="status-item">
                <div class="status-label">Errori Sessione</div>
                <div class="status-value" style="color:#c62828;">{st.session_state.score_ko}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        if session_tot > 0: st.progress(done / session_tot)
    
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
                if st.button("PROSSIMA DOMANDA ➡", type="primary", width="stretch"): 
                    next_question(); st.rerun()

            else:
                # MOSTRA OPZIONI
                for i, opt in enumerate(st.session_state.shuffled_options):
                    btn_label = opt['txt']
                    if "Vela" in st.session_state.quiz_mode: btn_label = f"⚪ {opt['txt']}"
                    if st.button(btn_label, key=f"btn_{i}", width="stretch"):
                        answer(opt['ok'], i); st.rerun()
                
                st.markdown("<br>", unsafe_allow_html=True)
                c_skip, c_idk = st.columns(2)
                with c_skip:
                    if st.session_state.exam_mode:
                        if st.button("⏭️ SALTA", width="stretch"): skip_current_question(); st.rerun()
                with c_idk:
                    if st.button("🚩 Non la so!", width="stretch"): answer(False, -1); st.rerun()
    
    if st.session_state.current_row is None: 
        if not st.session_state.exam_finished and st.session_state.current_user != "Comandante":
             # Non dovrebbe mai arrivare qui se l'autostart funziona, ma per sicurezza:
             st.info("👈 Seleziona un argomento per iniziare.")