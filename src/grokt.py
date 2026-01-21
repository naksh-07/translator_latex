import os
import json
import time
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm
from groq import Groq  # <-- NEW IMPORT

# -------------------------------
# ENV + API
# -------------------------------
load_dotenv()
# Note: Ab .env mein GROQ_API_KEY hona chahiye
API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("❌ Error: 'GROQ_API_KEY' not found in .env file")

# Initialize Groq Client
client = Groq(api_key=API_KEY)

CONFIG_PATH = Path("config/prompts.json")

# -------------------------------
# LOAD CONFIG (SAME LOGIC)
# -------------------------------
def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config missing: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

# -------------------------------
# SYSTEM INSTRUCTION (SAME LOGIC)
# -------------------------------
def build_system_instruction(config):
    settings = config["project_settings"]
    source_lang = settings["source_language"]
    target_lang = settings["target_language"]

    base = "\n".join(config["base_instructions"])
    # Fallback logic for style
    style = config["style_rules"].get("novel", "Translate accurately.")

    return (
        f"{base}\n\n"
        f"Source: {source_lang}\n"
        f"Target: {target_lang}\n\n"
        f"Style: {style}\n\n"
        f"Return only the translated text in Markdown."
    )

# -------------------------------
# TEXT CLEANUP (SAME LOGIC)
# -------------------------------
def clean_text(text):
    return text.replace("\r", "").replace("\ufeff", "").strip()

# -------------------------------
# HYBRID CHUNKING (SAME LOGIC)
# -------------------------------
def split_text_smartly(text, max_chars=7000):
    text = clean_text(text)

    if len(text) <= max_chars:
        return [text]

    paragraphs = text.split("\n")
    chunks = []
    current = ""
    
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue

        if len(para) > max_chars:
            sentences = para.split(". ")
            for s in sentences:
                if len(current) + len(s) + 2 > max_chars:
                    chunks.append(current.strip())
                    current = s + ". "
                else:
                    current += s + ". "
        else:
            if len(current) + len(para) + 2 > max_chars:
                chunks.append(current.strip())
                current = para + "\n"
            else:
                current += para + "\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks

# -------------------------------
# STRONG RETRY SYSTEM (UPDATED FOR GROQ)
# -------------------------------
def generate_with_retry(client, system_instr, user_prompt, max_retries=7):
    # Model ID set kar diya hai Llama 3.3 pe
    MODEL_ID = "llama-3.3-70b-versatile"
    
    for i in range(max_retries):
        try:
            # Groq Call Structure
            completion = client.chat.completions.create(
                model=MODEL_ID,
                messages=[
                    {"role": "system", "content": system_instr},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.5, # Thoda balanced temperature
                max_tokens=4096, # Llama 3.3 ka context bada hai
            )
            return completion.choices[0].message.content
            
        except Exception as e:
            err = str(e)
            wait = (i + 1) * 8

            # Rate Limit Handling (Groq ke liye zaroori hai)
            if "429" in err or "rate limit" in err.lower():
                print(f"⚠️ Rate Limit (Groq). Waiting {wait}s...")
                time.sleep(wait)
                continue
            elif "500" in err or "503" in err:
                print(f"⚠️ Server Error. Waiting {wait}s...")
                time.sleep(wait)
                continue
            else:
                print(f"❌ Fatal Error: {err}")
                return None

    return None

# -------------------------------
# OUTPUT SANITIZER (SAME LOGIC)
# -------------------------------
def sanitize_output(text):
    if not text:
        return ""

    bad_starts = [
        "Here is", "Translation:", "Translated:", 
        "Output:", "Sure,", "Okay,"
    ]
    for b in bad_starts:
        if text.lstrip().startswith(b):
            text = text.lstrip()[len(b):].strip()

    return text.strip()

# -------------------------------
# MAIN TRANSLATOR (UPDATED)
# -------------------------------
def translate_book():
    print("Loading settings...")
    config = load_config()

    input_dir = Path("data/raw_text")
    output_dir = Path("data/output_books")
    temp_dir = Path("data/temp")
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    files = sorted(input_dir.glob("*.txt"))
    if not files:
        print("No files found in raw_text")
        return

    # System Instruction Build karo
    system_instruction = build_system_instruction(config)

    previous_original = ""
    previous_translated = ""

    for file in tqdm(files, desc="Translating (Groq)"):
        output_file = output_dir / f"{file.stem}.md"
        temp_file = temp_dir / f"{file.stem}.partial.md"

        if output_file.exists():
            continue

        raw = clean_text(file.read_text(encoding="utf-8"))
        chunks = split_text_smartly(raw)

        final_output = ""

        for idx, chunk in enumerate(chunks):
            part = f"(Part {idx+1}/{len(chunks)})" if len(chunks) > 1 else ""

            # Prompt Construction (Same as before)
            prompt = f"""
---BEGIN---
Previous Original Context:
{previous_original[-1200:]}

Previous Translated Context:
{previous_translated[-1200:]}

Now translate the following {part}:

{chunk}
---END---
"""
            # Groq function call (Passing system instruction here)
            translated = generate_with_retry(client, system_instruction, prompt)

            if not translated:
                print(f"❌ Chunk failed: {idx+1}")
                continue

            translated = sanitize_output(translated)
            final_output += translated + "\n\n"

            # Update dual context
            previous_original = chunk[-1500:]
            previous_translated = translated[-1500:]

            # Partial save
            temp_file.write_text(final_output, encoding="utf-8")

            # Groq Free Tier Cooldown (Thoda safe side)
            time.sleep(3)

        # Final save
        output_file.write_text(final_output.strip(), encoding="utf-8")
        if temp_file.exists():
            temp_file.unlink()

    print("\n✔ DONE. Check the output_books folder.")


if __name__ == "__main__":
    translate_book()