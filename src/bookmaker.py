import markdown
import os
import webbrowser
from pathlib import Path

def create_ebook(book_title="My AI Novel"):
    input_dir = Path("data/output_books")
    
    # Filename clean karo
    clean_title = "".join(c for c in book_title if c.isalnum() or c in (' ', '_')).replace(' ', '_')
    output_html_path = Path(f"{clean_title}.html")
    
    # 1. Files Dhundo
    files = sorted(list(input_dir.glob("*.md")))
    
    if not files:
        print("⚠️ Bhai 'data/output_books' khaali hai!")
        return

    print(f"📚 Found {len(files)} chapters. Cooking up the E-Book...")

    # 2. Master Markdown String
    full_markdown = ""
    
    # Title Page
    full_markdown += f"""
<div class="title-page">
    <h1>{book_title}</h1>
    <p class="subtitle">Translated by AI & Naveen (The Tech Boss)</p>
</div>
<div class="page-break"></div>
"""

    for file in files:
        text = file.read_text(encoding="utf-8")
        # Har chapter ke liye div wrap
        full_markdown += f"\n\n<div class='chapter'>\n\n{text}\n\n</div><div class='page-break'></div>"

    # 3. Convert to HTML
    print("🔄 Converting Markdown to HTML...")
    html_body = markdown.markdown(full_markdown, extensions=['extra'])

    # 4. CSS Styling (Browser Friendly)
    css_style = """
    @import url('https://fonts.googleapis.com/css2?family=Hind:wght@300;400;700&family=Merriweather:ital,wght@0,300;0,700;1,300&display=swap');

    body {
        font-family: 'Hind', sans-serif;
        line-height: 1.8;
        color: #222;
        max-width: 800px; /* Reading width */
        margin: 0 auto;
        padding: 40px;
        background: #fff;
    }

    /* Print Specific Styles - Ye tab chalega jab tu PDF save karega */
    @media print {
        body { max-width: 100%; padding: 0; }
        .no-print { display: none !important; }
        .page-break { page-break-before: always; }
        a { text-decoration: none; color: #000; }
    }

    h1, h2, h3 {
        font-family: 'Merriweather', serif;
        color: #2c3e50;
        text-align: center;
    }

    .title-page {
        text-align: center;
        margin-top: 150px;
        margin-bottom: 200px;
    }
    
    h1 { font-size: 3em; margin-bottom: 0.2em; }
    .subtitle { font-size: 1.2em; color: #666; font-style: italic; }

    p {
        margin-bottom: 1.5em;
        text-align: justify;
        font-size: 12pt;
    }

    /* Drop Cap */
    h1 + p::first-letter, h2 + p::first-letter {
        font-size: 3.5em;
        float: left;
        margin-top: -10px;
        margin-right: 0.1em;
        line-height: 0.8;
    }

    /* Button Style */
    .print-btn {
        position: fixed;
        top: 20px;
        right: 20px;
        background: #e74c3c;
        color: white;
        padding: 10px 20px;
        border: none;
        border-radius: 5px;
        cursor: pointer;
        font-size: 16px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        z-index: 1000;
    }
    .print-btn:hover { background: #c0392b; }
    """

    # 5. Final HTML with Print Button
    final_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>{book_title}</title>
        <style>{css_style}</style>
    </head>
    <body>
        <button class="print-btn no-print" onclick="window.print()">🖨️ Save as PDF</button>
        {html_body}
    </body>
    </html>
    """

    output_html_path.write_text(final_html, encoding="utf-8")
    
    print(f"\n✅ DONE! Open this file in Chrome/Edge: {output_html_path.resolve()}")
    print("👉 File open kar aur upar 'Save as PDF' button daba dena. Best quality milegi!")
    
    # Try to open automatically
    try:
        webbrowser.open(f"file://{output_html_path.resolve()}")
    except:
        pass

if __name__ == "__main__":
    create_ebook(book_title="The Hobbit - Hindi Edition")