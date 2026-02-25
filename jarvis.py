import feedparser
import smtplib
import time
import os
import hashlib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

# ============================================================
# J.A.R.V.I.S. - Monitor de Oportunidades Upwork (RSS)
# Filtra: Data Entry + Automacao | $10-$50
# Notifica: luissuni18@gmail.com
# ============================================================

RSS_FEEDS = [
    "https://www.upwork.com/ab/feed/jobs/rss?q=data+entry&budget=10-50&sort=recency",
    "https://www.upwork.com/ab/feed/jobs/rss?q=automation+python&budget=10-50&sort=recency",
    "https://www.upwork.com/ab/feed/jobs/rss?q=data+entry+automation&sort=recency",
    "https://www.upwork.com/ab/feed/jobs/rss?q=web+scraping&budget=10-50&sort=recency",
]

SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
EMAIL_DEST = os.environ.get("EMAIL_DEST", "luissuni18@gmail.com")

seen_jobs = set()

def get_job_id(entry):
    return hashlib.md5(entry.get("link", entry.get("title", "")).encode()).hexdigest()

def extrair_budget(summary):
    import re
    matches = re.findall(r"\$([\d,]+)", summary or "")
    if matches:
        valores = [int(m.replace(",", "")) for m in matches]
        return min(valores), max(valores)
    return None, None

def budget_valido(entry):
    summary = entry.get("summary", "") + entry.get("title", "")
    min_val, max_val = extrair_budget(summary)
    if min_val is None:
        return True
    return min_val <= 50 and max_val >= 10

def enviar_email(job_title, job_link, job_summary, feed_source):
    if not SMTP_USER or not SMTP_PASS:
        print(f"[JARVIS] SMTP nao configurado. Vaga encontrada: {job_title}")
        return

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"JARVIS - Nova Vaga: {job_title[:60]}"
    msg["From"] = SMTP_USER
    msg["To"] = EMAIL_DEST

    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #14a800;">J.A.R.V.I.S. encontrou uma vaga!</h2>
        <h3>{job_title}</h3>
        <p><strong>Descricao:</strong><br>{job_summary[:500]}...</p>
        <p><a href="{job_link}" style="background:#14a800;color:white;padding:12px 24px;
           text-decoration:none;border-radius:4px;display:inline-block;">
           VER VAGA NO UPWORK</a></p>
        <hr>
        <p style="color:#666;font-size:12px;">
            Fonte: {feed_source}<br>
            Detectado em: {datetime.now().strftime("%d/%m/%Y %H:%M")} (Angola)
        </p>
    </body></html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, EMAIL_DEST, msg.as_string())
        print(f"[JARVIS] Email enviado: {job_title[:50]}")
    except Exception as e:
        print(f"[JARVIS] Erro ao enviar email: {e}")

def verificar_feeds():
    novos = 0
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                job_id = get_job_id(entry)
                if job_id in seen_jobs:
                    continue
                seen_jobs.add(job_id)
                if budget_valido(entry):
                    novos += 1
                    print(f"[JARVIS] Nova vaga: {entry.get('title', 'Sem titulo')[:60]}")
                    enviar_email(
                        job_title=entry.get("title", "Sem titulo"),
                        job_link=entry.get("link", "#"),
                        job_summary=entry.get("summary", "Sem descricao"),
                        feed_source=feed_url
                    )
        except Exception as e:
            print(f"[JARVIS] Erro no feed {feed_url}: {e}")
    return novos

def main():
    print("=" * 50)
    print("J.A.R.V.I.S. - Monitor Upwork RSS")
    print(f"Destino: {EMAIL_DEST}")
    print("Categorias: Data Entry, Automacao, Web Scraping")
    print("Budget: $10 - $50")
    print("=" * 50)

    ciclo = 0
    while True:
        ciclo += 1
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Ciclo #{ciclo} - Verificando feeds...")
        novos = verificar_feeds()
        print(f"[JARVIS] {novos} nova(s) vaga(s) encontrada(s) neste ciclo.")
        print(f"[JARVIS] Proxima verificacao em 30 minutos...")
        time.sleep(1800)

if __name__ == "__main__":
    main()
