import markdown
import os
from weasyprint import HTML, CSS
from pathlib import Path

def create_pdf(book_title="My AI Novel"):
    input_dir = Path("data/output_books")
    output_pdf_path = Path(f"{book_title.replace(' ', '_')}.pdf")
    
    # 1. Saare Translated Chapters dhundo
    # Pattern *_translated.md match karega
    files = sorted(list(input_dir.glob("*_translated.md")))
    
    if not files:
        print("⚠️ Bhai 'data/output_books' khaali hai! Pehle translate toh kar!")
        return

    print(f"📚 Found {len(files)} chapters. Merging content...")

    # 2. Master Markdown String Banao
    full_markdown = ""
    
    # Optional: Title Page Content
    full_markdown += f"# {book_title}\n\n*Translated by AI & Co-founder Naveen*\n\n---\n\n"

    for file in files:
        text = file.read_text(encoding="utf-8")
        # Har chapter ke baad page break logic (CSS ke liye class add kar rahe hain)
        full_markdown += f"\n\n<div class='page-break'></div>\n\n{text}"

    # 3. Markdown ko HTML me convert karo
    html_content = markdown.markdown(full_markdown, extensions=['extra'])

    # 4. Styling (The "Vibecode" CSS)
    # Hindi Fonts ke liye Google Fonts import kiya hai (Hind/Noto Sans)
    css_style = """
    @import url('https://fonts.googleapis.com/css2?family=Hind:wght@300;400;700&family=Merriweather:ital,wght@0,300;0,700;1,300&display=swap');

    @page {
        size: A5; /* Novel size standard */
        margin: 2cm;
        @bottom-center {
            content: counter(page); /* Page Numbers */
            font-family: 'Hind', sans-serif;
            font-size: 10pt;
            color: #555;
        }
    }

    body {
        font-family: 'Hind', sans-serif; /* Hindi friendly font */
        font-size: 12pt;
        line-height: 1.6;
        color: #222;
        background-color: #fff; /* Paper color */
    }

    h1, h2, h3 {
        font-family: 'Merriweather', serif; /* Headings thode fancy */
        color: #2c3e50;
        text-align: center;
        margin-top: 1.5em;
    }

    h1 { font-size: 24pt; border-bottom: 2px solid #eee; padding-bottom: 10px; }
    
    p {
        margin-bottom: 1em;
        text-align: justify; /* Professional book look */
    }

    /* Code blocks agar technical book ho */
    pre {
        background: #f4f4f4;
        padding: 10px;
        border-radius: 5px;
        font-family: 'Courier New', monospace;
    }

    .page-break {
        page-break-before: always;
    }
    """

    # 5. Final HTML Wrapping
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css_style}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    print("🎨 Rendering PDF... (Isme thoda time lag sakta hai)")
    
    # 6. Generate PDF
    HTML(string=final_html).write_pdf(output_pdf_path)
    
    print(f"\n✅ SAHI HAI BOSS! PDF Ready hai: {output_pdf_path.resolve()}")

if __name__ == "__main__":
    create_pdf(book_title="The AI Journey")