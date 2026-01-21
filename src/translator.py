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
    """JSON se settings load karta hai"""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"❌ Config file nahi mili: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def build_system_instruction(config):
    """
    Ye function 'Lego Blocks' jod kar final prompt banata hai.
    """
    settings = config["project_settings"]
    
    # 1. Base Rules (Jo hamesha same rahenge)
    base = "\n".join(config["base_instructions"])
    
    # 2. Dynamic Rules (JSON se uthaye hue)
    source_lang = settings["source_language"]
    target_lang = settings["target_language"]
    
    genre_rule = config["genres"].get(settings["selected_genre"], "")
    vibe_rule = config["vibes"].get(settings["selected_vibe"], "")

    # 3. Final Assembly
    instruction = f"""
    {base}
    
    --- PROJECT SETTINGS ---
    Source Language: {source_lang}
    Target Language: {target_lang}
    
    --- SPECIFIC INSTRUCTIONS ---
    GENRE ({settings['selected_genre']}): 
    {genre_rule}
    
    VIBE/TONE ({settings['selected_vibe']}): 
    {vibe_rule}
    
    --- CRITICAL RULE ---
    Translate from {source_lang} to {target_lang} strictly adhering to the VIBE defined above.
    """
    return instruction

def translate_book():
    # Load configuration
    print("⚙️ Loading configuration...")
    config = load_config()
    
    # Paths setup
    input_dir = Path("data/raw_text")
    output_dir = Path("data/output_books")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Files gather karna
    files = sorted(list(input_dir.glob("*.txt")))
    if not files:
        print("⚠️ Koi text files nahi mili 'data/raw_text' me. Pehle extraction run kar!")
        return

    # Build the Brain (Prompt)
    system_instruction = build_system_instruction(config)
    print(f"\n🧠 AI Instructions Built:\nStyle: {config['project_settings']['selected_vibe']}\nTarget: {config['project_settings']['target_language']}\n")

    # Initialize Model (gemini-flash-latest for speed)
    model = genai.GenerativeModel(
        model_name="gemini-flash-latest",
        system_instruction=system_instruction
    )

    last_context = "Start of the book."
    
    # The Loop
    for file in tqdm(files, desc="Translating..."):
        output_file = output_dir / f"{file.stem}_translated.md"
        
        # Resume capability
        if output_file.exists():
            continue

        raw_text = file.read_text(encoding="utf-8")
        
        # User Prompt (Dynamic content + Context)
        user_prompt = f"""
        PREVIOUS CONTEXT:
        {last_context}
        
        ---
        TEXT TO TRANSLATE:
        {raw_text}
        """

        try:
            # AI Call
            response = model.generate_content(user_prompt)
            translated_text = response.text
            
            # Save
            output_file.write_text(translated_text, encoding="utf-8")
            
            # Context Update (Simple Logic)
            last_context = translated_text[-800:]
            
            # Rate Limit Protection
            time.sleep(4) 

        except Exception as e:
            print(f"❌ Error in {file.name}: {e}")
            time.sleep(10) # Error aane pe thoda lamba break

    print(f"\n✅ Translation Complete! Files saved in: {output_dir}")

if __name__ == "__main__":
    translate_book()