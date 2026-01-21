import fitz  # PyMuPDF
import re
import json
import shutil  # Folder saaf karne ke liye
from pathlib import Path

def clean_and_extract(pdf_path, output_dir):
    """
    Ab ye function 'Smart' hai. Ye nakli/chote chapters ko ignore karega.
    """
    print(f"📂 Processing: {pdf_path}")
    
    # 0. Safai Abhiyan (Purana kachra saaf karo)
    if output_dir.exists():
        shutil.rmtree(output_dir) # Purana folder delete
    output_dir.mkdir(parents=True, exist_ok=True) # Naya banao

    # 1. PDF Load karo
    doc = fitz.open(pdf_path)
    full_text = ""
    
    print("⏳ Extracting text layer... (thoda time lagega)")
    for page in doc:
        text = page.get_text("text")
        
        # --- CLEANING ---
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            # Page numbers filter
            if len(line.strip()) < 4 and line.strip().isdigit():
                continue 
            cleaned_lines.append(line)
        
        full_text += "\n".join(cleaned_lines) + "\n"

    # 2. Smart Chapter Detection
    pattern = r"^(?:Chapter|CHAPTER|अध्याय|Section)\s+(?:\d+|[IVX]+).*"
    matches = list(re.finditer(pattern, full_text, flags=re.MULTILINE))

    if not matches:
        print("⚠️ Koi Chapter headings nahi mili! Puri book ek file me save hogi.")
        (output_dir / "full_book.txt").write_text(full_text, encoding="utf-8")
        return

    print(f"🔥 Found {len(matches)} Potential Chapters. Filtering junk now...")
    
    valid_chapter_count = 0  # Isse count karenge asli chapters
    
    for i, match in enumerate(matches):
        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        
        chapter_content = full_text[start:end]
        
        # --- 🚧 THE BOUNCER LOGIC (Game Changer) 🚧 ---
        # Agar chapter me 100 words se kam hain, toh wo Chapter nahi hai (TOC/Header hai)
        word_count = len(chapter_content.split())
        if word_count < 100:
            print(f"🗑️ Skipped Junk/Header: {match.group().strip()} (Only {word_count} words)")
            continue

        # Agar pass ho gaya, toh save karo
        valid_chapter_count += 1
        
        chapter_title = match.group().strip().replace(" ", "_").replace(":", "")
        safe_filename = "".join([c for c in chapter_title if c.isalnum() or c in "_"])
        
        # Filename me 'valid_chapter_count' use karenge taaki sequence (01, 02) na tute
        file_path = output_dir / f"{valid_chapter_count:02d}_{safe_filename}.txt"
        file_path.write_text(chapter_content, encoding="utf-8")
        print(f"✅ Saved: {file_path.name} ({word_count} words)")

def generate_metadata(raw_text_dir, output_file="data/metadata.json"):
    print("\n📊 Generating Metadata report...")
    raw_path = Path(raw_text_dir)
    files = sorted(list(raw_path.glob("*.txt")))
    
    if not files:
        print("⚠️ Koi files nahi mili!")
        return

    total_words = 0
    chapters_info = []

    for f in files:
        text = f.read_text(encoding="utf-8")
        word_count = len(text.split())
        total_words += word_count
        chapters_info.append({"filename": f.name, "word_count": word_count, "status": "pending"})

    metadata = {
        "project_name": "My AI Book",
        "total_chapters": len(files),
        "total_words": total_words,
        "average_words_per_chapter": total_words // len(files) if files else 0,
        "chapters": chapters_info
    }

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
    print(f"✅ Metadata saved! Total Real Chapters: {len(files)}")

if __name__ == "__main__":
    pdf_file = "data/input_pdfs/The Hobbt.pdf"
    out_path = Path("data/raw_text")
    if Path(pdf_file).exists():
        clean_and_extract(pdf_file, out_path)
        generate_metadata(out_path)
    else:
        print("❌ PDF Missing!")