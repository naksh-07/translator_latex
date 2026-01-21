import sys
import time
import os
from pathlib import Path
from colorama import init, Fore, Style

# Apne modules import karte hain
from src.cleaner import clean_and_extract, generate_metadata
from src.translator import translate_book
from src.bookmaker import create_pdf

# Color init (Windows support ke liye)
init(autoreset=True)

# --- DESI UTILS ---
def print_banner():
    banner = f"""
    {Fore.CYAN}╔══════════════════════════════════════════════════╗
    {Fore.CYAN}║    🚀  AI NOVEL TRANSLATOR 3000 (ULTIMATE)   ║
    {Fore.CYAN}║       Created by: Naveen (Tech Co-founder)   ║
    {Fore.CYAN}╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
    """
    print(banner)

def print_step(msg):
    print(f"\n{Fore.YELLOW}⚡ [PROCESS] {msg}{Style.RESET_ALL}")

def print_success(msg):
    print(f"{Fore.GREEN}✅ [SUCCESS] {msg}{Style.RESET_ALL}")

def print_error(msg):
    print(f"{Fore.RED}❌ [ERROR] {msg}{Style.RESET_ALL}")

def check_env():
    if not Path(".env").exists():
        print_error("Bhai .env file missing hai! API Key kahan se laau?")
        sys.exit(1)

# --- CORE FUNCTIONS ---

def step_1_extract():
    print_step("Extraction Mode Initiated...")
    
    # Auto-detect PDF in input folder
    input_dir = Path("data/input_pdfs")
    pdfs = list(input_dir.glob("*.pdf"))
    
    if not pdfs:
        print_error("Folder 'data/input_pdfs' khaali hai! PDF daal wahan.")
        return False
    
    # Agar multiple hain toh pehli utha lo (ya user se pucho - abhi simple rakhte hain)
    target_pdf = pdfs[0]
    print(f"📄 Target PDF detected: {Fore.WHITE}{target_pdf.name}")
    
    # Process
    output_dir = Path("data/raw_text")
    clean_and_extract(target_pdf, output_dir)
    generate_metadata(output_dir)
    return True

def step_2_translate():
    print_step("Connecting to Gemini AI Brain...")
    # Translator script call
    try:
        translate_book()
        print_success("Translation Phase Complete!")
        return True
    except Exception as e:
        print_error(f"Translation fat gayi: {e}")
        return False

def step_3_publish():
    print_step("Generating Final Professional PDF...")
    try:
        # PDF Name user se pucho ya default
        book_title = input(f"{Fore.CYAN}📘 Book ka Title kya rakhna hai? (Enter for Default): {Style.RESET_ALL}").strip()
        if not book_title:
            book_title = "My_AI_Novel"
        
        create_pdf(book_title)
        return True
    except Exception as e:
        print_error(f"Publishing failed: {e}")
        return False

# --- MAIN MENU ---

def main():
    os.system('cls' if os.name == 'nt' else 'clear') # Screen saaf
    check_env()
    print_banner()

    while True:
        print(f"\n{Fore.MAGENTA}Select a Mission, Boss:{Style.RESET_ALL}")
        print("1. 📄 Extract Text from PDF")
        print("2. 🤖 Translate with AI (Gemini)")
        print("3. 📕 Publish PDF (Markdown to PDF)")
        print(f"{Fore.GREEN}4. 🚀 GOD MODE (Run All Steps){Style.RESET_ALL}")
        print("5. 🚪 Exit")
        
        choice = input(f"\n{Fore.CYAN}Enter choice [1-5]: {Style.RESET_ALL}")

        start_time = time.time()

        if choice == '1':
            step_1_extract()
        
        elif choice == '2':
            step_2_translate()
        
        elif choice == '3':
            step_3_publish()
        
        elif choice == '4':
            print(f"\n{Fore.GREEN}🔥 GOD MODE ACTIVATED! Hold tight...{Style.RESET_ALL}")
            if step_1_extract():
                if step_2_translate():
                    step_3_publish()
            print(f"\n{Fore.CYAN}✨ Total Time: {round(time.time() - start_time, 2)} seconds")
            
        elif choice == '5':
            print("Bye Bhai! Happy Coding! 👋")
            break
        
        else:
            print_error("Galat button daba diya. Phir se try kar.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n🛑 Process rok diya gaya.")