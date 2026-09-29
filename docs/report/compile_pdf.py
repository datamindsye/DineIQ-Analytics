"""
DineIQ Analytics - PDF Compiler
Compiles DineIQ_Analytics_Technical_Report.html into publication-quality DineIQ_Analytics_Technical_Report.pdf
Team: Data Minds 0.2
"""

import os
import sys
import asyncio
import pathlib
import re
from playwright.async_api import async_playwright

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(REPORT_DIR, "DineIQ_Analytics_Technical_Report.html")
PDF_PATH = os.path.join(REPORT_DIR, "DineIQ_Analytics_Technical_Report.pdf")

def verify_assets():
    print(f"Checking HTML file at: {HTML_PATH}")
    if not os.path.exists(HTML_PATH):
        raise FileNotFoundError(f"HTML file not found: {HTML_PATH}")
    
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()
    
    # Find all referenced image sources
    srcs = re.findall(r'src=["\']([^"\']+)["\']', html)
    print(f"Total embedded media references found in HTML: {len(srcs)}")
    
    missing = []
    for src in srcs:
        if src.startswith("http://") or src.startswith("https://"):
            continue
        # Local path relative to docs/report/
        local_path = os.path.join(REPORT_DIR, src)
        if not os.path.exists(local_path):
            missing.append((src, local_path))
    
    if missing:
        print(f"WARNING: {len(missing)} missing assets detected:")
        for src, lp in missing:
            print(f"  - {src} -> {lp}")
    else:
        print("All referenced media assets verified on disk!")

async def compile_to_pdf():
    verify_assets()
    
    print("Launching Playwright Chromium...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Create page with desktop viewport
        page = await browser.new_page(viewport={"width": 1280, "height": 1800})
        
        file_uri = pathlib.Path(HTML_PATH).as_uri()
        print(f"Loading document: {file_uri}")
        await page.goto(file_uri, wait_until="networkidle")
        
        # Give Google Fonts and SVG renderings time to settle
        await asyncio.sleep(2)
        
        print("Rendering publication-quality PDF...")
        header_template = """
        <div style="font-size: 7.5pt; color: #64748b; width: 100%; display: flex; justify-content: space-between; padding: 0 15mm; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px;">
            <span>DineIQ Analytics | Data Minds 0.2</span>
            <span>Data Science Intelligence Arena</span>
        </div>
        """
        
        footer_template = """
        <div style="font-size: 7.5pt; color: #64748b; width: 100%; display: flex; justify-content: space-between; padding: 0 15mm; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; border-top: 1px solid #e2e8f0; padding-top: 4px;">
            <span>Technical Project Report — TechWiz 7</span>
            <span>Page <span class="pageNumber"></span> of <span class="totalPages"></span></span>
        </div>
        """
        
        await page.pdf(
            path=PDF_PATH,
            format="A4",
            print_background=True,
            display_header_footer=True,
            header_template=header_template,
            footer_template=footer_template,
            margin={"top": "18mm", "bottom": "18mm", "left": "15mm", "right": "15mm"}
        )
        
        await browser.close()
        
    print(f"PDF successfully compiled to: {PDF_PATH}")
    file_size_mb = os.path.getsize(PDF_PATH) / (1024 * 1024)
    print(f"PDF Size: {file_size_mb:.2f} MB")

if __name__ == "__main__":
    asyncio.run(compile_to_pdf())
