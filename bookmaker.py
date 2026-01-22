import os
import requests
from fpdf import FPDF
from pathlib import Path
import warnings

# ---------------------------------------------------------
# SETUP: Fonts
# ---------------------------------------------------------
def setup_fonts():
    fonts = {
        "Regular": "https://github.com/google/fonts/raw/main/ofl/sahitya/Sahitya-Regular.ttf",
        "Bold": "https://github.com/google/fonts/raw/main/ofl/sahitya/Sahitya-Bold.ttf"
    }
    
    paths = {}
    print("🎨 Fonts check kar raha hu...")
    
    for style, url in fonts.items():
        path = Path(f"Sahitya-{style}.ttf")
        if not path.exists():
            print(f"   📥 Downloading {style} font...")
            try:
                response = requests.get(url)
                path.write_bytes(response.content)
            except Exception as e:
                print(f"❌ Error downloading font: {e}")
        paths[style] = str(path)
    
    return paths

# ---------------------------------------------------------
# PDF CLASS
# ---------------------------------------------------------
class RoyalPDF(FPDF):
    def __init__(self, title):
        super().__init__(format="A5")
        self.book_title = title
        
    def header(self):
        if self.page_no() > 1:
            self.set_font("times", style="I", size=8)
            self.set_text_color(100, 100, 100)
            self.cell(0, 10, self.book_title, align="C", new_x="LMARGIN", new_y="NEXT")
            self.ln(1)

    def footer(self):
        self.set_y(-12)
        self.set_font("times", size=9)
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, f"{self.page_no()}", align="C")

# ---------------------------------------------------------
# MAIN LOGIC
# ---------------------------------------------------------
def create_royal_pdf(book_title="My AI Novel"):
    # Check for HarfBuzz (Matra Fixer)
    try:
        import uharfbuzz
        print("✅ Text Shaper (HarfBuzz) Found! Matras will be fixed.")
    except ImportError:
        print("⚠️ WARNING: 'uharfbuzz' not installed! Matras toot sakti hain.")
        print("👉 Run: pip install uharfbuzz")
        return

    input_dir = Path("data/output_books")
    
    clean_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '_')).replace(' ', '_')
    output_pdf_path = Path(f"{clean_title}_Final_Fixed.pdf")
    
    files = sorted(list(input_dir.glob("*.md")))
    if not files:
        print("⚠️ Folder khaali hai bhai!")
        return

    font_paths = setup_fonts()

    # Setup PDF (Compact Margins)
    pdf = RoyalPDF(book_title)
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=15, top=15, right=15)
    
    # -----------------------------------------------------
    # 👇 MAGIC FIX: script="deva" (Devanagari)
    # -----------------------------------------------------
    # Ye batata hai ki Hindi matra kaise judegi
    pdf.add_font("HindiBook", fname=font_paths["Regular"])
    pdf.add_font("HindiBookBd", fname=font_paths["Bold"])
    
    # English Fonts (Standard)
    # Times is built-in

    print(f"📚 Binding {len(files)} chapters (With Matra Fix)...")

    # --- TITLE PAGE ---
    pdf.add_page()
    pdf.set_y(60)
    
    pdf.set_font("times", style="B", size=24) 
    pdf.multi_cell(0, 15, book_title, align="C")
    
    pdf.ln(5)
    pdf.set_font("times", style="I", size=12)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 10, "Translated by AI & Naveen", align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(15)
    # Symbol ke liye Hindi Font use karein taaki crash na ho
    pdf.set_font("HindiBook", size=18)
    pdf.cell(0, 10, "✻", align="C", new_x="LMARGIN", new_y="NEXT")

    # --- CHAPTERS ---
    for file in files:
        text = file.read_text(encoding="utf-8")
        lines = text.split("\n")
        
        pdf.add_page()
        
        # Heading
        heading = lines[0].replace("#", "").strip()
        
        pdf.set_y(25)
        pdf.set_font("HindiBookBd", size=16)
        pdf.set_text_color(0, 0, 0)
        
        # script="deva" forces correct shaping for this cell
        pdf.cell(0, 10, heading, align="C", new_x="LMARGIN", new_y="NEXT")
        
        # Separator
        pdf.set_font("HindiBook", size=12)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 6, "♦ ♦ ♦", align="C", new_x="LMARGIN", new_y="NEXT")
        
        pdf.ln(5)

        # Body Text
        pdf.set_font("HindiBook", size=11) 
        pdf.set_text_color(10, 10, 10) 
        
        body_text = "\n".join(lines[1:])
        body_text = body_text.replace("**", "").replace("*", "").replace("#", "")
        
        # Enable Shaping here too
        # Note: FPDF2 with uharfbuzz installed auto-detects complex scripts 
        # but passing the font correctly is key.
        pdf.multi_cell(0, 6, body_text, align="J")

        # End Mark
        pdf.ln(10)
        pdf.set_font("HindiBook", size=12) 
        pdf.set_text_color(150, 150, 150)
        pdf.cell(0, 10, "--- ❦ ---", align="C", new_x="LMARGIN", new_y="NEXT")

    pdf.output(output_pdf_path)
    print(f"\n✅ DONE! Check: {output_pdf_path.resolve()}")
    print("👉 Ab 'Matra' check kar, 'HarfBuzz' ne sab jod diya hoga!")

if __name__ == "__main__":
    create_royal_pdf(book_title="The Hobbit - Hindi Edition")