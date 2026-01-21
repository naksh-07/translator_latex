import os
import json
import time
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# -------------------------------
# ENV + API
# -------------------------------
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("API Key not found in .env")

genai.configure(api_key=API_KEY)

CONFIG_PATH = Path("config/prompts.json")


# -------------------------------
# LOAD CONFIG
# -------------------------------
def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config missing: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


# -------------------------------
# SYSTEM INSTRUCTION (Compact)
# -------------------------------
def build_system_instruction(config):
    settings = config["project_settings"]
    source_lang = settings["source_language"]
    target_lang = settings["target_language"]

    base = "\n".join(config["base_instructions"])
    style = config["style_rules"]["novel"]

    return (
        f"{base}\n\n"
        f"Source: {source_lang}\n"
        f"Target: {target_lang}\n\n"
        f"Style: {style}\n\n"
        f"Return only the translated text in Markdown."
    )


# -------------------------------
# TEXT CLEANUP
# -------------------------------
def clean_text(text):
    # Remove BOM & normalize
    return text.replace("\r", "").replace("\ufeff", "").strip()


# -------------------------------
# HYBRID CHUNKING (Paragraph + Sentence)
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

        # Very long paragraph → break into sentences
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
# STRONG RETRY SYSTEM (Free Tier Safe)
# -------------------------------
def generate_with_retry(model, prompt, max_retries=7):
    for i in range(max_retries):
        try:
            res = model.generate_content(prompt)
            return res.text
        except Exception as e:
            err = str(e)
            wait = (i + 1) * 8

            if "429" in err or "exhausted" in err or "Quota" in err:
                print(f"⚠️ Rate Limit. Waiting {wait}s...")
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
# MAIN TRANSLATOR
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

    system_instruction = build_system_instruction(config)

    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash",
        system_instruction=system_instruction
    )

    previous_original = ""
    previous_translated = ""

    for file in tqdm(files, desc="Translating"):
        output_file = output_dir / f"{file.stem}.md"
        temp_file = temp_dir / f"{file.stem}.partial.md"

        if output_file.exists():
            continue

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
                print(f"❌ Chunk failed: {idx+1}")
                continue

            translated = sanitize_output(translated)
            final_output += translated + "\n\n"

            # Update dual context
            previous_original = chunk[-1500:]
            previous_translated = translated[-1500:]

            # Partial save (safety)
            temp_file.write_text(final_output, encoding="utf-8")

            # Free tier cooldown
            time.sleep(4)

        # Final save
        output_file.write_text(final_output.strip(), encoding="utf-8")
        if temp_file.exists():
            temp_file.unlink()

    print("\n✔ DONE. Check the output_books folder.")


if __name__ == "__main__":
    translate_book()
