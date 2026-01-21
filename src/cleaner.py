import fitz  # PyMuPDF
import re
import json  # <--- YE MISSING THA (JSON banane ke liye zaroori hai)
from pathlib import Path

def clean_and_extract(pdf_path, output_dir):
    """
    Ye function PDF se text nikalta hai, headers/footers hatata hai, 
    aur Chapters me divide karta hai.
    """
    print(f"📂 Processing: {pdf_path}")
    
    # 1. PDF Load karo
    doc = fitz.open(pdf_path)
    full_text = ""
    
    print("⏳ Extracting text layer... (thoda time lagega)")
    for page in doc:
        text = page.get_text("text")
        
        # --- DESI JUGAD FOR CLEANING ---
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Page numbers filter (Basic logic)
            if len(line.strip()) < 4 and line.strip().isdigit():
                continue 
            cleaned_lines.append(line)
        
        full_text += "\n".join(cleaned_lines) + "\n"

    # 2. Smart Chapter Detection
    pattern = r"^(?:Chapter|CHAPTER|अध्याय|Section)\s+(?:\d+|[IVX]+).*"
    matches = list(re.finditer(pattern, full_text, flags=re.MULTILINE))

    # Agar koi Chapter heading nahi mili
    if not matches:
        print("⚠️ Koi Chapter headings nahi mili! Puri book ek file me save hogi.")
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "full_book.txt").write_text(full_text, encoding="utf-8")
        return

    print(f"🔥 Found {len(matches)} Chapters! Splitting now...")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        
        chapter_title = match.group().strip().replace(" ", "_").replace(":", "")
        # Filename safe banao
        safe_filename = "".join([c for c in chapter_title if c.isalnum() or c in "_"])
        
        chapter_content = full_text[start:end]
        
        # File save (01_Chapter_1.txt format)
        file_path = output_dir / f"{i+1:02d}_{safe_filename}.txt"
        file_path.write_text(chapter_content, encoding="utf-8")
        print(f"✅ Saved: {file_path.name}")

def generate_metadata(raw_text_dir, output_file="data/metadata.json"):
    """
    Chapters count karega aur ek JSON report banayega.
    """
    print("\n📊 Generating Metadata report...")
    raw_path = Path(raw_text_dir)
    
    # Saari text files dhundo
    files = sorted(list(raw_path.glob("*.txt")))
    
    if not files:
        print("⚠️  Koi files nahi mili metadata ke liye!")
        return

    total_words = 0
    chapters_info = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        word_count = len(text.split())
        total_words += word_count
        
        chapters_info.append({
            "filename": f.name,
            "word_count": word_count,
            "status": "pending"
        })

    metadata = {
        "project_name": "My AI Book",
        "total_chapters": len(files),
        "total_words": total_words,
        "average_words_per_chapter": total_words // len(files) if files else 0,
        "chapters": chapters_info
    }

    # JSON file save karo
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    
    print(f"✅ Metadata saved to {output_file}! Total Words: {total_words}")

# --- EXECUTION AREA ---
if __name__ == "__main__":
    # 1. Setup Paths
    pdf_file = "data/input_pdfs/sample.pdf"
    out_path = Path("data/raw_text")
    
    # 2. Check File
    if Path(pdf_file).exists():
        # Step A: Clean & Extract
        clean_and_extract(pdf_file, out_path)
        
        # Step B: Generate Stats (Ye ab chalega!)
        generate_metadata(out_path)
        
        print("\n🚀 Extraction Complete! Ab Translator.py chalao.")
    else:
        print(f"❌ Bhai, '{pdf_file}' nahi mili. 'data/input_pdfs' me PDF daal pehle!")