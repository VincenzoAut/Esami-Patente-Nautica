# Registro allievi su Supabase + avvisi Telegram/email
import json
import smtplib
import urllib.request
from email.message import EmailMessage

import streamlit as st

import database as db_engine


def _rpc(name, params):
    sb = db_engine.init_connection()
    if not sb:
        return None
    try:
        res = sb.rpc(name, params).execute()
        return res.data
    except Exception as exc:
        print(f"RPC {name} non disponibile: {exc}")
        return None


def list_students():
    data = _rpc("list_students", {})
    if not data:
        return []
    return [{"user_id": str(r["user_id"]), "display_name": str(r["display_name"])} for r in data]


def login_student(name, pin):
    data = _rpc("login_student", {"p_name": name, "p_pin": pin})
    if isinstance(data, dict):
        return data
    return None


def admin_login(pin):
    data = _rpc("admin_login", {"p_pin": pin})
    if isinstance(data, dict):
        return data
    return {"ok": False, "error": "Funzione non disponibile"}


def request_access(name, email):
    data = _rpc("request_access", {"p_name": name, "p_email": email})
    if isinstance(data, dict):
        return data
    return {"ok": False, "error": "Funzione non disponibile"}


def admin_list_deleted(admin_pin):
    data = _rpc("admin_list_deleted", {"p_admin": admin_pin})
    return data or []


def admin_restore_student(name, admin_pin):
    data = _rpc("admin_restore_student", {"p_name": name, "p_admin": admin_pin})
    if isinstance(data, dict):
        return data
    return {"ok": False, "error": "Funzione non disponibile"}


def admin_add_student(name, email, pin, admin_pin):
    data = _rpc("admin_add_student", {
        "p_name": name, "p_email": email, "p_pin": pin, "p_admin": admin_pin,
    })
    if isinstance(data, dict):
        return data
    return {"ok": False, "error": "Funzione non disponibile"}


def admin_list_students(admin_pin):
    data = _rpc("admin_list_students", {"p_admin": admin_pin})
    return data or []


def admin_list_requests(admin_pin):
    data = _rpc("admin_list_requests", {"p_admin": admin_pin})
    return data or []


def admin_reset_pin(name, new_pin, admin_pin):
    data = _rpc("admin_reset_pin", {
        "p_name": name, "p_new_pin": new_pin, "p_admin": admin_pin,
    })
    if isinstance(data, dict):
        return data
    return {"ok": False, "error": "Funzione non disponibile"}


def admin_delete_student(name, admin_pin, delete_history=True):
    data = _rpc("admin_delete_student", {
        "p_name": name, "p_admin": admin_pin, "p_delete_history": delete_history,
    })
    if isinstance(data, dict):
        return data
    return {"ok": False, "error": "Funzione non disponibile"}


def send_telegram(name, email):
    try:
        cfg = st.secrets["telegram"]
        token = str(cfg["token"])
        chat_id = str(cfg["chat_id"])
    except Exception:
        return False

    testo = "🔔 Richiesta di accesso - Patente Nautica\nNome: " + name + "\nEmail: " + email + "\n\nPer approvare rispondi al bot: approva <email> <PIN>"
    payload = json.dumps({"chat_id": chat_id, "text": testo}).encode("utf-8")
    req = urllib.request.Request(
        "https://api.telegram.org/bot" + token + "/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return bool(json.load(resp).get("ok"))
    except Exception as exc:
        print(f"Telegram errore: {exc}")
        return False


def send_alert(name, email):
    try:
        cfg = st.secrets["email"]
        host = str(cfg["smtp_host"])
        port = int(cfg.get("smtp_port", 587))
        user = str(cfg["username"])
        pwd = str(cfg["password"])
        dest = str(cfg.get("to", user))
    except Exception:
        return False

    msg = EmailMessage()
    msg["Subject"] = "Patente Nautica: richiesta di accesso da " + name
    msg["From"] = user
    msg["To"] = dest
    msg.set_content(
        "Nuova richiesta di accesso all'app Patente Nautica.\n\n"
        "Nome: " + name + "\nEmail: " + email + "\n\n"
        "Apri il pannello istruttore per approvarla."
    )
    try:
        with smtplib.SMTP(host, port, timeout=15) as srv:
            srv.starttls()
            srv.login(user, pwd)
            srv.send_message(msg)
        return True
    except Exception as exc:
        print(f"Invio email fallito: {exc}")
        return False


def notify_access(name, email):
    canali = []
    if send_telegram(name, email):
        canali.append("Telegram")
    if send_alert(name, email):
        canali.append("email")
    return canali
