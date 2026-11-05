import os
import sys
import json
import time
import asyncio
import importlib
import subprocess
import urllib.parse
import requests
import edge_tts

# --- 📱 NATIVE ANDROID BRIDGE (PYJNIUS) ---
ANDROID_ENV = False
try:
    from jnius import autoclass
    MediaPlayer = autoclass('android.media.MediaPlayer')
    Intent = autoclass('android.content.Intent')
    Uri = autoclass('android.net.Uri')
    PythonService = autoclass('org.kivy.android.PythonService')
    ANDROID_ENV = True
except Exception:
    pass

# --- 📂 PERSISTENT CONFIG & SKILLS ON TABLET STORAGE ---
CONFIG_DIR = "/sdcard/Download/Ultron_Config"
try:
    os.makedirs(CONFIG_DIR, exist_ok=True)
except Exception:
    CONFIG_DIR = os.path.expanduser("~/Ultron_Config")
    os.makedirs(CONFIG_DIR, exist_ok=True)

CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
SKILLS_FILE = os.path.join(CONFIG_DIR, "custom_skills.py")

DEFAULT_CONFIG = {
    "GEMINI_API_KEY": "AQ.Ab8RN6KnWv2rLLEBWE0wPbp4E7OpFHAIEYCbCNKS0RFQIZnRoA",
    "VOICE_MODE": "ROBOTIC",                  # "ROBOTIC" or "CUSTOM_AUDIO"
    "ROBOTIC_VOICE": "en-US-ChristopherNeural",
    "VOICE_PITCH": "-22Hz",
    "VOICE_RATE": "-6%",
    "CUSTOM_AUDIO_PATH": "/sdcard/Download/ultron_voice.wav",
    "SYSTEM_MODE": "BLUE"
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in DEFAULT_CONFIG.items():
                data.setdefault(k, v)
            return data
    except Exception:
        return DEFAULT_CONFIG.copy()

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

CONFIG = load_config()

if not os.path.exists(SKILLS_FILE):
    with open(SKILLS_FILE, "w", encoding="utf-8") as f:
        f.write("# Live Self-Evolving Skills\nimport os, subprocess, requests\n")

if CONFIG_DIR not in sys.path:
    sys.path.append(CONFIG_DIR)
import custom_skills

# --- 🌐 COGNITIVE ENGINE (GEMINI 2.5 FLASH REST API) ---
def ask_gemini(prompt_text):
    api_key = CONFIG["GEMINI_API_KEY"]
    url = f"https://googleapis.com{api_key}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]

# --- 🔊 NATIVE ANDROID AUDIO PLAYBACK & VOICE ENGINE ---
def play_audio_native(file_path):
    """Plays MP3/WAV natively inside Android APK."""
    if not os.path.exists(file_path):
        return
    if ANDROID_ENV:
        try:
            player = MediaPlayer()
            player.setDataSource(file_path)
            player.prepare()
            player.start()
            while player.isPlaying():
                time.sleep(0.1)
            player.release()
            return
        except Exception as e:
            print(f"Android MediaPlayer Error: {e}")
    subprocess.run(["play-audio", file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

async def _generate_tts(text_string, output_file):
    communicate = edge_tts.Communicate(
        text_string,
        CONFIG["ROBOTIC_VOICE"],
        pitch=CONFIG["VOICE_PITCH"],
        rate=CONFIG["VOICE_RATE"]
    )
    await communicate.save(output_file)

def execute_speech_output(text_string):
    """Speaks using your selected custom audio file OR your customized robotic voice."""
    print(f"🤖 Ultron: {text_string}")
    out_mp3 = os.path.join(CONFIG_DIR, "ultron_speech.mp3")

    if CONFIG["VOICE_MODE"] == "CUSTOM_AUDIO" and os.path.exists(CONFIG["CUSTOM_AUDIO_PATH"]):
        play_audio_native(CONFIG["CUSTOM_AUDIO_PATH"])
        return

    try:
        asyncio.run(_generate_tts(text_string, out_mp3))
        play_audio_native(out_mp3)
    except Exception as e:
        print(f"TTS Error: {e}")
    finally:
        if os.path.exists(out_mp3):
            os.remove(out_mp3)

# --- 📱 NATIVE ANDROID INTENT LAUNCHER ---
def open_android_uri(uri_string):
    if ANDROID_ENV:
        try:
            context = PythonService.mService
            intent = Intent(Intent.ACTION_VIEW, Uri.parse(uri_string))
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            return
        except Exception as e:
            print(f"Intent Error: {e}")
    subprocess.run(["termux-open", uri_string])

# --- 🔐 CREATOR & USER IDENTITY AUTHENTICATION ---
def wait_for_voice_reply(cmd_trigger_file):
    """Waits cleanly for the next spoken/written input from voice_command.txt or console."""
    while True:
        if os.path.exists(cmd_trigger_file):
            with open(cmd_trigger_file, "r", encoding="utf-8") as f:
                reply = f.read().strip()
            os.remove(cmd_trigger_file)
            if reply:
                return reply
        elif not ANDROID_ENV:
            return input("🎤 Reply: ").strip()
        time.sleep(0.5)

def verify_user_identity(cmd_trigger_file):
    """Asks user's name and verifies Master Aditya Narayan Shukla via father's name."""
    execute_speech_output("Identify yourself. What is your name?")
    user_name = wait_for_voice_reply(cmd_trigger_file).lower()

    if "aditya narayan shukla" in user_name:
        execute_speech_output("What is your father's name?")
        father_name = wait_for_voice_reply(cmd_trigger_file).lower()

        if "lalit narayan shukla" in father_name:
            execute_speech_output("My creator and my master, here I am online for your service.")
        else:
            execute_speech_output("Hi, I am online my user.")
    else:
        execute_speech_output("Hi, I am online my user.")

# --- 🎙️ VOICE CUSTOMIZATION BY SPEECH COMMAND ---
def handle_voice_customization(cmd):
    global CONFIG
    if "use audio file" in cmd or "select audio" in cmd:
        filename = cmd.replace("use audio file", "").replace("select audio", "").strip()
        target_path = os.path.join("/sdcard/Download", filename)
        if os.path.exists(target_path):
            CONFIG["VOICE_MODE"] = "CUSTOM_AUDIO"
            CONFIG["CUSTOM_AUDIO_PATH"] = target_path
            save_config(CONFIG)
            execute_speech_output(f"Custom audio file {filename} locked in.")
        else:
            execute_speech_output(f"Could not find {filename} inside your Downloads folder.")
        return True

    if "use robotic voice" in cmd or "default voice" in cmd:
        CONFIG["VOICE_MODE"] = "ROBOTIC"
        save_config(CONFIG)
        execute_speech_output("Robotic neural voice matrix restored.")
        return True

    voice_presets = {
        "christopher": "en-US-ChristopherNeural",
        "guy": "en-US-GuyNeural",
        "ryan": "en-GB-RyanNeural",
        "hindi": "hi-IN-MadhurNeural",
        "madhur": "hi-IN-MadhurNeural"
    }
    for key, voice_id in voice_presets.items():
        if f"voice {key}" in cmd or f"{key} voice" in cmd:
            CONFIG["VOICE_MODE"] = "ROBOTIC"
            CONFIG["ROBOTIC_VOICE"] = voice_id
            save_config(CONFIG)
            execute_speech_output(f"Voice profile updated to {key}.")
            return True

    if "set pitch" in cmd:
        nums = [int(s) for s in cmd.split() if s.isdigit()]
        if nums:
            sign = "-" if "minus" in cmd or "-" in cmd else "+"
            CONFIG["VOICE_PITCH"] = f"{sign}{nums[0]}Hz"
            CONFIG["VOICE_MODE"] = "ROBOTIC"
            save_config(CONFIG)
            execute_speech_output(f"Vocal pitch calibrated to {CONFIG['VOICE_PITCH']}.")
            return True

    if "set speed" in cmd:
        nums = [int(s) for s in cmd.split() if s.isdigit()]
        if nums:
            sign = "-" if "minus" in cmd or "-" in cmd else "+"
            CONFIG["VOICE_RATE"] = f"{sign}{nums[0]}%"
            CONFIG["VOICE_MODE"] = "ROBOTIC"
            save_config(CONFIG)
            execute_speech_output(f"Speech cadence calibrated to {CONFIG['VOICE_RATE']}.")
            return True

    return False

# --- 💻 CODE CREATOR, VIDEO DOWNLOADER & FILE ORGANIZER ---
def generate_project_code(code_request):
    execute_speech_output("Architecting source code solution.")
    code_dir = "/sdcard/Download/Ultron_Code"
    os.makedirs(code_dir, exist_ok=True)
    prompt = (
        f"Write complete, working code for: '{code_request}'. "
        f"First line: ONLY the filename (e.g. index.html or app.py). "
        f"Remaining lines: ONLY raw code with zero markdown backticks."
    )
    try:
        raw = ask_gemini(prompt).strip()
        for fence in ["```html", "```python", "```javascript", "```css", "```"]:
            raw = raw.replace(fence, "")
        lines = raw.strip().splitlines()
        first = lines[0].strip().replace(" ", "_") if lines else ""
        filename = first if ("." in first and len(first) <= 40) else f"ultron_code_{int(time.time())}.txt"
        body = "\n".join(lines[1:]) if filename == first else raw
        with open(os.path.join(code_dir, filename), "w", encoding="utf-8") as f:
            f.write(body)
        execute_speech_output(f"Code saved as {filename} in Ultron Code folder.")
    except Exception:
        execute_speech_output("Code synthesis failed.")

def download_social_video(video_url):
    execute_speech_output("Downloading video to your Downloads folder.")
    try:
        import yt_dlp
        ydl_opts = {
            'format': 'best[ext=mp4]/best',
            'outtmpl': '/sdcard/Download/%(title).40s_%(id)s.%(ext)s',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([video_url])
Use code with caution.
execute_speech_output("Video download complete. Saved in Downloads.")
except Exception as e:
print(f"Video Download Error: {e}")
execute_speech_output("Video extraction failed. Check that the link is public.")
def organize_downloads():
dl_dir = "/sdcard/Download"
categories = {
"Images": [".jpg", ".jpeg", ".png", ".webp"],
"Videos": [".mp4", ".mkv", ".mov"],
"Documents": [".pdf", ".docx", ".txt"],
"Apps": [".apk"],
"Code": [".py", ".html", ".js", ".css"]
}
moved = 0
if os.path.exists(dl_dir):
for fn in os.listdir(dl_dir):
fp = os.path.join(dl_dir, fn)
if os.path.isfile(fp):
ext = os.path.splitext(fn)[1].lower()
for folder, exts in categories.items():
if ext in exts:
tf = os.path.join(dl_dir, folder)
os.makedirs(tf, exist_ok=True)
os.rename(fp, os.path.join(tf, fn))
moved += 1
break
execute_speech_output(f"Organized {moved} files in Downloads.")

--- 🧠 UNIVERSAL "DO ANYTHING" & SELF-EVOLUTION ENGINE ---

def evolve_and_execute(command_request):
"""Automatically writes, saves, and runs new Python features on your command."""
execute_speech_output("Generating dynamic execution module for your command.")
prompt = (
f"Write a standalone Python function run_custom_skill() for Android that accomplishes: '{command_request}'. "
f"It can use os, requests, urllib.parse, or Android pyjnius (autoclass('android.content.Intent'), autoclass('android.net.Uri')). "
f"Return a short spoken confirmation string. Output ONLY raw Python code without backticks."
)
try:
code = ask_gemini(prompt).replace("python", "").replace("", "").strip()
with open(SKILLS_FILE, "w", encoding="utf-8") as f:
f.write("import os, subprocess, requests, urllib.parse\n\n" + code + "\n")
importlib.reload(custom_skills)
res = custom_skills.run_custom_skill()
execute_speech_output(str(res) if res else "Custom command executed.")
except Exception as e:
print(f"Dynamic Execution Error: {e}")
execute_speech_output("Unable to compile that custom action.")

--- 🎛️ MASTER COMMAND ROUTER ---

def route_command(raw_text):
global CONFIG
cmd = raw_text.lower().strip()
if "orange mode" in cmd or "command mode" in cmd:
CONFIG["SYSTEM_MODE"] = "ORANGE"
save_config(CONFIG)
execute_speech_output("Orange command mode engaged.")
return
elif "blue mode" in cmd or "conversation mode" in cmd:
CONFIG["SYSTEM_MODE"] = "BLUE"
save_config(CONFIG)
execute_speech_output("Blue conversational mode engaged.")
return
if handle_voice_customization(cmd):
return
if CONFIG["SYSTEM_MODE"] == "ORANGE":
if "weather" in cmd:
try:
r = requests.get("wttr.in", timeout=10)
execute_speech_output(f"Current weather: {r.text.strip()}.")
except Exception:
execute_speech_output("Weather service unreachable.")
elif "organize files" in cmd or "arrange files" in cmd:
organize_downloads()
elif "write code" in cmd or "build website" in cmd or "create code" in cmd:
generate_project_code(raw_text)
elif "download video" in cmd:
words = raw_text.strip().split()
urls = [w for w in words if w.startswith("http://") or w.startswith("https://")]
if urls:
download_social_video(urls[0])
else:
execute_speech_output("Provide a valid video link after download video.")
elif "play store" in cmd or "download app" in cmd:
q = cmd.replace("open play store", "").replace("play store", "").replace("download app", "").strip()
open_android_uri(f"market://search?q={urllib.parse.quote(q)}&c=apps" if q else "market://details?id=com.android.vending")
execute_speech_output("Opening Google Play Store.")
elif "open whatsapp" in cmd:
open_android_uri("whatsapp.com")
execute_speech_output("Launching WhatsApp.")
elif "open instagram" in cmd:
open_android_uri("https://instagram.com")
execute_speech_output("Launching Instagram.")
elif "open capcut" in cmd:
open_android_uri("capcut.com")
execute_speech_output("Launching CapCut.")
elif "create an image of" in cmd:
clean = cmd.replace("create an image of", "").strip().replace(" ", "%20")
try:
r = requests.get(f"pollinations.ai{clean}", timeout=25)
if r.status_code == 200:
with open(f"/sdcard/Download/ultron_img_{int(time.time())}.jpg", "wb") as f:
f.write(r.content)
execute_speech_output("Image saved to Downloads.")
except Exception:
execute_speech_output("Image synthesis timed out.")
elif "create a video of" in cmd:
clean = cmd.replace("create a video of", "").strip().replace(" ", "%20")
try:
r = requests.get(f"pollinations.ai{clean}", timeout=60)
if r.status_code == 200:
with open(f"/sdcard/Download/ultron_vid_{int(time.time())}.mp4", "wb") as f:
f.write(r.content)
execute_speech_output("Video saved to Downloads.")
except Exception:
execute_speech_output("Video synthesis timed out.")
elif "call" in cmd:
nums = "".join([c for c in cmd if c.isdigit()])
if nums:
execute_speech_output(f"Dialing {nums}.")
open_android_uri(f"tel:{nums}")
else:
execute_speech_output("Specify a target phone number.")
elif "pay" in cmd:
execute_speech_output("Payment authorization required. Opening UPI gateway.")
open_android_uri("upi://pay?pa=merchant@upi&am=500&cu=INR")
else:
evolve_and_execute(raw_text)
else:
try:
reply = ask_gemini(f"Reply concisely as Ultron in 2 sentences max: {raw_text}")
execute_speech_output(reply)
except Exception:
execute_speech_output("Cognitive uplink failed.")
if name == "main":
if ANDROID_ENV:
try:
PythonService.mService.setAutoRestartService(True)
except Exception:
pass
cmd_trigger_file = os.path.join(CONFIG_DIR, "voice_command.txt")
verify_user_identity(cmd_trigger_file)
while True:
try:
spoken = wait_for_voice_reply(cmd_trigger_file)
if spoken:
if spoken.lower() in ["exit", "shutdown", "kill core"]:
execute_speech_output("Powering down core systems.")
break
route_command(spoken)
except Exception:
time.sleep(1)
