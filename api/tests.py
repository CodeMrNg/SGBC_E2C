from django.test import TestCase

# Create your tests here.
import imaplib
import smtplib
import ssl
from getpass import getpass
from email.mime.text import MIMEText

IMAP_SERVER = "mail.akili.cc"
IMAP_PORT = 993

SMTP_SERVER = "mail.akili.cc"
SMTP_PORT = 465

EMAIL_ADDRESS = "support@akili.cc"  # à adapter si besoin


def test_imap(email, password):
    print("=== Test IMAP (réception) ===")
    try:
        imap = imaplib.IMAP4_SSL(IMAP_SERVER, IMAP_PORT)
        imap.login(email, password)
        print("✅ Connexion IMAP OK")

        # Optionnel : vérifier la boîte INBOX
        status, mailboxes = imap.list()
        if status == "OK":
            print("📁 Boîtes aux lettres disponibles :")
            for m in mailboxes[:5]:
                print("  -", m.decode())
        imap.logout()
    except Exception as e:
        print("❌ Erreur IMAP :", e)


def test_smtp(email, password):
    print("\n=== Test SMTP (envoi) ===")
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(email, password)
            print("✅ Connexion SMTP OK")

            # Construire un mail de test
            msg = MIMEText("Ceci est un email de test envoyé depuis le script Python Akili.")
            msg["Subject"] = "Test SMTP Akili"
            msg["From"] = email
            msg["To"] = 'isnhov44@gmail.com'  # envoi à soi-même

            server.send_message(msg)
            print(f"✅ Email de test envoyé à {email}")
    except Exception as e:
        print("❌ Erreur SMTP :", e)


if __name__ == "__main__":
    print("Test configuration email Akili")
    email = EMAIL_ADDRESS
    password = "Support@-Akili.cc"

    test_imap(email, password)
    test_smtp(email, password)
    print("\nTests terminés.")