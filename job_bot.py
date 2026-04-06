import os
import time
import json
import csv
import smtplib
import hashlib
from datetime import datetime
from email.message import EmailMessage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager
from openai import OpenAI

# --- CONFIGURATION ---
OPENAI_API_KEY = "your openai api key here" # Use your OpenAI API key
EMAIL_ADDRESS = "your email here"  # Use your Gmail address
EMAIL_PASSWORD = "your email app password here"  # Use a Gmail App Password
RESUME_PATH = r"your resume path here"  # Path to your resume file (e.g., "C:/Users/You/Documents/Resume.docx")
WHATSAPP_GROUP = "your whatsapp group name here"  # Exact name of the WhatsApp group to monitor
CHECK_INTERVAL = 900  # 15 minutes
HASH_LOG_FILE = "processed_messages.log"

client = OpenAI(api_key=OPENAI_API_KEY)

def get_processed_hashes():
    """Maintains a persistent record of analyzed messages."""
    if os.path.exists(HASH_LOG_FILE):
        with open(HASH_LOG_FILE, "r") as f:
            return set(line.strip() for line in f)
    return set()

def log_processed_hash(msg_hash):
    with open(HASH_LOG_FILE, "a") as f:
        f.write(msg_hash + "\n")

def analyze_job_text(job_description):
    """Generates application-ready content using the Expert Recruiter prompt."""
    # Context to help the AI map your specific skills
    my_profile_context = "Expertise: GenAI, LLMs, RAG, Python, Prompt Engineering. Goal: Apply to high-level AI roles."

    user_prompt = f"""
Role:
You are an expert Technical Recruiter and Resume Strategist.

Task:
I will provide:
1) A Job Description (JD): {job_description}
2) My Resume / Profile: {my_profile_context}

Your task is to generate application-ready content.
add specific details after the email body section. here are my specific details:
Current Location: 
Work Authorization: 
Professional Experience: 
Availability: Immediate Joiner

STRICT OUTPUT RULES:
• Plain text only
• NO HTML tags (<b>, <br>, etc.)
• NO markdown bold (**)
• Use UNICODE BOLD characters (e.g. 𝐛𝐨𝐥𝐝) for emphasis
• No emojis
• No filler explanations
• No extra commentary
• Use clear markdown headings
• Output must be directly copy-paste ready for Gmail/Outlook/LinkedIn

Generate EXACTLY the following sections, in this order:

---
## Recruiter Email
## Recruiter Phone
## Email Subject Line
## Email Body
## specific details
(End with a SIGNATURE section that includes a polite closing with name, mail, phone each in their own line) 

---

Return the final result as a JSON object with these keys:
"recruiter_email": "extracted email or 'Not provided'",
"recruiter_phone": "extracted phone or 'N/A'",
"subject": "the generated subject line",
"body": "the generated email body content",
"should_apply": true/false
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": user_prompt}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return None

def send_email(to_email, subject, body):
    """Composes and sends the email with the attached resume."""
    if not to_email or "@" not in to_email:
        return False
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to_email
    msg.set_content(body)
    
    try:
        with open(RESUME_PATH, 'rb') as f:
            file_data = f.read()
            msg.add_attachment(file_data, maintype='application', 
                           subtype='vnd.openxmlformats-officedocument.wordprocessingml.document', 
                           filename="LakshmiSowjanyaResume.docx")        
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Sending Error: {e}")
        return False

def get_driver():
    """Initializes Chrome with a persistent profile to maintain WhatsApp login."""
    options = Options()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    bot_data_path = os.path.join(script_dir, "BotProfile")
    options.add_argument(f"--user-data-dir={bot_data_path}")
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def scroll_to_top_of_day(driver):
    """Uses a JavaScript executor to scroll the active chat pane directly."""
    try:
        # This JS finds the scrollable element by looking for the one with the most height 
        # inside the main chat area, which is the most reliable way to find the message list.
        script = """
        var main = document.querySelector('#main');
        var scrollable = main.querySelector('div[overflow-y="scroll"]') || 
                         main.querySelector('div[style*="overflow-y: scroll"]');
        if(!scrollable) {
            scrollable = document.querySelector('div._amig') || 
                         document.querySelector('div[aria-label="Message list"]');
        }
        if(scrollable) {
            scrollable.scrollTop = scrollable.scrollTop - 2000;
            return true;
        }
        return false;
        """
        success = driver.execute_script(script)
        if success:
            time.sleep(2)
    except Exception as e:
        print(f"Scroll Warning: {e}")

def run_bot():
    driver = get_driver()
    driver.get("https://web.whatsapp.com")
    print(">>> ACTION: Scan the QR code now if you haven't already.")
    
    # Wait for the main interface to load
    WebDriverWait(driver, 120).until(EC.presence_of_element_located((By.XPATH, '//div[@id="pane-side"]')))
    print("Login confirmed!")

    while True:
        try:
            print(f"\n--- Starting Cycle at {datetime.now().strftime('%H:%M:%S')} ---")
            
            # WhatsApp metadata date format check
            # Use Inspect Element on a message to see if it's MM/DD/YYYY or DD/MM/YYYY
            prefix = '#' if os.name == 'nt' else '-'

            today_formats = [
                # This matches exactly what your debug output shows: 4/6/2026
                datetime.now().strftime(f'%{prefix}m/%{prefix}d/%Y'), 
                # This matches the reverse: 6/4/2026
                datetime.now().strftime(f'%{prefix}d/%{prefix}m/%Y'),
                # Keep standard formats just in case
                datetime.now().strftime('%m/%d/%Y'),
                datetime.now().strftime('%d/%m/%Y'),
                "Today"
            ]
            processed_hashes = get_processed_hashes()
            
            # 1. Search for and Open the Group
            # Use a more reliable search box selector
            js_search = "return document.querySelector('div[contenteditable=\"true\"][data-tab=\"3\"]') || document.querySelector('div[role=\"textbox\"]');"
            search_box = driver.execute_script(js_search)
            
            if not search_box:
                actions = ActionChains(driver)
                actions.move_by_offset(200, 150).click().perform()
                actions.move_by_offset(-200, -150).perform()
                search_box = driver.switch_to.active_element

            search_box.click()
            search_box.send_keys(Keys.CONTROL + "a")
            search_box.send_keys(Keys.BACKSPACE)
            search_box.send_keys(WHATSAPP_GROUP)
            time.sleep(5)
            
            # 2. Open Group
            try:
                driver.find_element(By.XPATH, f"//span[@title='{WHATSAPP_GROUP}']").click()
                print(f"Opened {WHATSAPP_GROUP}")
            except:
                search_box.send_keys(Keys.ENTER)

            time.sleep(6)

            # 2. Scroll to load history
            scroll_to_top_of_day(driver)
            time.sleep(2)

            # 3. Identify Message Containers
            # 'copyable-text' is usually stable, but let's use a fallback for the text itself
            messages = driver.find_elements(By.CSS_SELECTOR, "div.copyable-text")
            print(f"Scanned {len(messages)} potential messages.")

            new_found = 0
            for msg in messages:
                try:
                    metadata = msg.get_attribute("data-pre-plain-text")
                    if not metadata:
                        continue
                    
                    is_today = any(fmt in metadata for fmt in today_formats)
                    
                    if is_today:
                        # FIX: Try to get text from the container itself if the span isn't there
                        try:
                            # First attempt: standard selectable text span
                            msg_text = msg.find_element(By.CSS_SELECTOR, "span.selectable-text").text
                        except:
                            # Fallback: Get all text within the bubble container
                            msg_text = msg.text
                        
                        # Remove the metadata from the message text if it got caught in msg.text
                        msg_text = msg_text.strip()
                        
                        if not msg_text:
                            continue

                        msg_id = hashlib.md5((metadata + msg_text).strip().encode('utf-8')).hexdigest()
                        
                        if msg_id not in processed_hashes:
                            # ... (rest of your logic: keywords, AI analysis, email)
                            keywords = ["hiring", "job", "requirement", "opening", "cv", "resume", "@"]
                            if any(k in msg_text.lower() for k in keywords):
                                print(f"Analyzing: {msg_text[:50]}...")
                                job_data = analyze_job_text(msg_text)
                                
                                if job_data and job_data.get("should_apply") and "@" in str(job_data.get("recruiter_email")):
                                    if send_email(job_data['recruiter_email'], job_data['subject'], job_data['body']):
                                        print(f"SUCCESS: Applied to {job_data['recruiter_email']}")
                            
                            log_processed_hash(msg_id) 
                            processed_hashes.add(msg_id)
                            new_found += 1

                except Exception as e:
                    # This will now only catch critical failures, not missing spans
                    continue

            if new_found == 0:
                print("No new qualified JDs found for today.")

            print(f"Cycle finished. Waiting {CHECK_INTERVAL//60} minutes...")
            time.sleep(CHECK_INTERVAL)
            driver.refresh()
            time.sleep(15)

        except Exception as e:
            print(f"Loop Error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_bot()