# 🤖 WhatsApp-to-Email Job Application Bot

An automated pipeline that monitors WhatsApp Web for job postings, analyzes them using OpenAI's GPT-4o, and automatically sends tailored email applications with an attached resume.

---

## 🚀 Overview
This bot automates the tedious parts of job hunting in high-volume WhatsApp groups:
1. **Monitors** a specific WhatsApp group for today's messages.
2. **Filters** messages using keywords (e.g., "hiring," "CV," "requirement").
3. **Analyzes** the job description using AI to extract recruiter contact info and assess fit.
4. **Drafts** a professional email using "Expert Recruiter" logic.
5. **Dispatches** the application via Gmail with your resume attached.

---

## 🛠️ Features
* **Persistent Login:** Uses a local Selenium profile (`BotProfile`) so you don't have to scan the QR code every time you run the script.
* **AI Intelligence:** Leverages GPT-4o to parse unstructured WhatsApp messages into clean JSON data.
* **Duplicate Prevention:** Uses MD5 hashing to log processed messages and avoid applying to the same post twice.
* **Safe Scrolling:** Includes a custom JavaScript executor to scroll through WhatsApp Web's virtualized list.
* **Professional Formatting:** Generates "plain text" bolding using Unicode characters for maximum compatibility across email clients.

---

## 📋 Prerequisites
* **Python 3.8+**
* **Google Chrome** installed.
* **OpenAI API Key** (with credits).
* **Gmail App Password:** If using Gmail, you must enable 2FA and generate an [App Password](https://myaccount.google.com/apppasswords).

---

## ⚙️ Configuration
Before running, update the constants in the `# --- CONFIGURATION ---` section of the script:

| Variable | Description |
| :--- | :--- |
| `OPENAI_API_KEY` | Your OpenAI secret key. |
| `EMAIL_ADDRESS` | The Gmail address used to send applications. |
| `EMAIL_PASSWORD` | Your 16-character Gmail App Password. |
| `RESUME_PATH` | The full local path to your `.docx` resume. |
| `WHATSAPP_GROUP` | The exact name of the WhatsApp group to monitor. |
| `CHECK_INTERVAL` | Time (in seconds) between scans (default: 900s / 15 mins). |

---

