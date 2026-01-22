import os
import json
import time
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# -------------------------------
# ENV + API SETUP
# -------------------------------
# Bhai, .env file check kar lena, API Key wahi honi chahiye!
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("❌ Error: API Key nahi mili! .env file check kar bhai.")

genai.configure(api_key=API_KEY)

CONFIG_PATH = Path("config/prompts.json")


# -------------------------------
# LOAD CONFIG
# -------------------------------
def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"❌ Config missing: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------
# SYSTEM INSTRUCTION
# -------------------------------
def build_system_instruction(config):
    settings = config["project_settings"]
    source_lang = settings["source_language"]
    target_lang = settings["target_language"]

    base = "\n".join(config["base_instructions"])
    
    # Style rules ko text mein convert kar rahe hain
    style_rules = config["style_rules"]
    style_text = ""
    
    if "novel" in style_rules:
        style_text = style_rules["novel"]
    else:
        for key, value in style_rules.items():
            style_text += f"- **{key.capitalize()}**: {value}\n"

    return (
        f"Role: Professional Literary Translator\n\n"
        f"Project Settings:\n"
        f"- Source: {source_lang}\n"
        f"- Target: {target_lang}\n\n"
        f"Base Instructions:\n{base}\n\n"
        f"Style Guidelines:\n{style_text}\n\n"
        f"Output Requirement:\nReturn ONLY the translated text in clean Markdown format."
    )


# -------------------------------
# TEXT CLEANUP
# -------------------------------
def clean_text(text):
    # Kachra saaf karne ka function
    return text.replace("\r", "").replace("\ufeff", "").strip()


# -------------------------------
# HYBRID CHUNKING (Smart Split)
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

        # Agar paragraph bahut bada hai toh sentence pe todenge
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
# STRONG RETRY SYSTEM
# -------------------------------
def generate_with_retry(model, prompt, max_retries=7):
    for i in range(max_retries):
        try:
            res = model.generate_content(prompt)
            return res.text
        except Exception as e:
            err = str(e)
            wait = (i + 1) * 8 # Thoda wait badha diya safety ke liye

            if "429" in err or "exhausted" in err or "Quota" in err:
                print(f"⚠️ Quota Full / Rate Limit. Waiting {wait}s... (Chai pee le tab tak ☕)")
                time.sleep(wait)
                continue
            else:
                print(f"❌ Fatal Error: {err}")
                return None

    return None


# -------------------------------
# OUTPUT SANITIZER
# -------------------------------
def sanitize_output(text):
    if not text:
        return ""

    bad_starts = [
        "Here is", "Translation:", "Translated:", 
        "Output:", "Sure,", "Okay,"
    ]
    for b in bad_starts:
        if text.startswith(b):
            text = text[len(b):].strip()

    return text.strip()


# -------------------------------
# MAIN TRANSLATOR (UPDATED LOGIC HERE)
# -------------------------------
def translate_book():
    print("⚙️ Settings load ho rahi hain...")
    config = load_config()

    input_dir = Path("data/raw_text")
    output_dir = Path("data/output_books")
    temp_dir = Path("data/temp")
    
    # Folders bana lo agar nahi hain
    output_dir.mkdir(parents=True, exist_ok=True)
    temp_dir.mkdir(parents=True, exist_ok=True)

    # 1. Saare files scan karo
    all_files = sorted(input_dir.glob("*.txt"))
    if not all_files:
        print("❌ 'data/raw_text' folder khali hai bhai!")
        return

    # 2. FILTER LOGIC: Jo ban chuka hai use skip karo
    files_to_process = []
    print(f"🔍 Checking {len(all_files)} files...")

    skipped_count = 0
    for file in all_files:
        output_file = output_dir / f"{file.stem}.md"
        
        # Check: File exist karti hai AND khali nahi hai
        if output_file.exists() and output_file.stat().st_size > 0:
            skipped_count += 1
        else:
            files_to_process.append(file)

    if skipped_count > 0:
        print(f"⏩ Skipped {skipped_count} files (Already Translated).")

    if not files_to_process:
        print("\n🎉 Badhai ho! Saari files already translated hain. Project Complete! ✅")
        return

    print(f"🚀 Starting translation for {len(files_to_process)} remaining files...\n")

    # 3. Model Setup
    system_instruction = build_system_instruction(config)
    
    # Model config for safety
    generation_config = genai.types.GenerationConfig(
        temperature=0.3, # Thoda creative kam, accurate zyada
    )

    model = genai.GenerativeModel(
        model_name="gemini-flash-latest", # Latest stable model name use kar
        system_instruction=system_instruction,
        generation_config=generation_config
    )

    previous_original = ""
    previous_translated = ""

    # 4. Processing Loop (Sirf bachi hui files pe)
    for file in tqdm(files_to_process, desc="Translating"):
        output_file = output_dir / f"{file.stem}.md"
        temp_file = temp_dir / f"{file.stem}.partial.md"

        raw = clean_text(file.read_text(encoding="utf-8"))
        chunks = split_text_smartly(raw)

        final_output = ""

        for idx, chunk in enumerate(chunks):
            part = f"(Part {idx+1}/{len(chunks)})" if len(chunks) > 1 else ""

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
            translated = generate_with_retry(model, prompt)

            if not translated:
                print(f"❌ Chunk failed in {file.name}. Skipping to next file...")
                break # Agar ek chunk fail hua toh poora file kharab ho sakta hai, break better hai

            translated = sanitize_output(translated)
            final_output += translated + "\n\n"

            # Context update
            previous_original = chunk[-1500:]
            previous_translated = translated[-1500:]

            # Partial save (Backup)
            temp_file.write_text(final_output, encoding="utf-8")

            # Free tier cooldown (Rohit Sharma mode: Slow but steady)
            time.sleep(4)

        # Final save jab saare chunks ho jayein
        if final_output:
            output_file.write_text(final_output.strip(), encoding="utf-8")
            if temp_file.exists():
                temp_file.unlink() # Temp file uda do

    print("\n✅ MISSION ACCOMPLISHED. Saare books 'output_books' folder mein check kar le.")


if __name__ == "__main__":
    translate_book()