import os
import json
import time
import google.generativeai as genai
from pathlib import Path
from dotenv import load_dotenv
from tqdm import tqdm

# 1. Setup & Environment
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("🚨 Bhai API Key gayab hai! .env check kar.")

genai.configure(api_key=API_KEY)

# Config path
CONFIG_PATH = Path("config/prompts.json")

def load_config():
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"❌ Config file nahi mili: {CONFIG_PATH}")
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_system_instruction(config):
    settings = config["project_settings"]
    base = "\n".join(config["base_instructions"])
    source_lang = settings["source_language"]
    target_lang = settings["target_language"]
    genre_rule = config["genres"].get(settings["selected_genre"], "")
    vibe_rule = config["vibes"].get(settings["selected_vibe"], "")

    return f"""
    {base}
    --- PROJECT SETTINGS ---
    Source: {source_lang} | Target: {target_lang}
    --- STYLE GUIDE ---
    GENRE: {genre_rule}
    VIBE: {vibe_rule}
    --- CRITICAL RULE ---
    Translate strictly adhering to the VIBE. Output ONLY the translated text in Markdown.
    """

# --- 🧠 SMART CHUNKING LOGIC ---
def split_text_smartly(text, max_chars=10000):
    """
    Agar chapter bahut bada hai, toh usse paragraphs me todta hai.
    Taaki Output Token Limit hit na ho.
    """
    if len(text) < max_chars:
        return [text]
    
    print(f"   ✂️  Chapter too big ({len(text)} chars). Splitting into chunks...")
    chunks = []
    current_chunk = []
    current_length = 0
    
    # Paragraphs pe split karo taaki sentence na tute
    paragraphs = text.split('\n')
    
    for para in paragraphs:
        # +2 for newline characters
        if current_length + len(para) + 2 > max_chars:
            chunks.append("\n".join(current_chunk))
            current_chunk = [para]
            current_length = len(para)
        else:
            current_chunk.append(para)
            current_length += len(para) + 2
            
    if current_chunk:
        chunks.append("\n".join(current_chunk))
        
    return chunks

# --- 🔁 RETRY LOGIC ---
def generate_with_retry(model, prompt, retries=3):
    """
    Agar API fail ho (Rate Limit), toh wait karke retry karega.
    """
    for i in range(retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) or "Resource has been exhausted" in str(e):
                wait_time = (i + 1) * 10  # 10s, 20s, 30s wait
                print(f"   ⚠️  Rate Limit Hit! Cooling down for {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"   ❌  Error: {e}")
                return None # Skip this chunk if error is weird
    return None

def translate_book():
    print("⚙️ Loading configuration...")
    config = load_config()
    
    input_dir = Path("data/raw_text")
    output_dir = Path("data/output_books")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    files = sorted(list(input_dir.glob("*.txt")))
    if not files:
        print("⚠️ Koi text files nahi mili 'data/raw_text' me.")
        return

    system_instruction = build_system_instruction(config)
    
    # Model Setup (Flash 1.5 is best for this)
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=system_instruction
    )

    last_context = "Start of the book."
    
    for file in tqdm(files, desc="Translating Chapters"):
        output_file = output_dir / f"{file.stem}_translated.md"
        
        if output_file.exists():
            continue

        raw_text = file.read_text(encoding="utf-8")
        
        # 1. Text ko Chunks me todo (Agar zaroorat ho)
        text_chunks = split_text_smartly(raw_text)
        final_translated_text = ""
        
        for index, chunk in enumerate(text_chunks):
            # Context me batao ki ye kaunsa part hai
            part_info = f"(Part {index+1}/{len(text_chunks)})" if len(text_chunks) > 1 else ""
            
            user_prompt = f"""
            PREVIOUS CONTEXT (Story so far):
            {last_context}
            
            ---
            TEXT TO TRANSLATE {part_info}:
            {chunk}
            """
            
            # 2. Call API with Retry
            translated_chunk = generate_with_retry(model, user_prompt)
            
            if translated_chunk:
                final_translated_text += translated_chunk + "\n\n"
                # Context update (Last 1000 chars)
                last_context = translated_chunk[-1000:]
            else:
                print(f"❌ Failed to translate chunk {index+1} of {file.name}")
            
            # 3. Rate Limit Sleep (Free tier safety)
            # Har chunk ke baad 5 second ruko.
            time.sleep(5) 

        # Save Final Chapter
        if final_translated_text:
            output_file.write_text(final_translated_text, encoding="utf-8")

    print(f"\n✅ Translation Complete! Files saved in: {output_dir}")

if __name__ == "__main__":
    translate_book()