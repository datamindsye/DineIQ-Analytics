"""
DineIQ Analytics - HTML to Markdown Report Converter
Converts DineIQ_Analytics_Technical_Report.html into GitHub Flavored Markdown (DineIQ_Analytics_Technical_Report.md)
Team: Data Minds 0.2
"""

import os
import re
from html.parser import HTMLParser

REPORT_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(REPORT_DIR, "DineIQ_Analytics_Technical_Report.html")
MD_PATH = os.path.join(REPORT_DIR, "DineIQ_Analytics_Technical_Report.md")

def clean_text(text):
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def html_to_markdown():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    md_lines = []
    
    # 1. Header / Title Block
    md_lines.append("# DINEIQ ANALYTICS")
    md_lines.append("## Data Science Intelligence Arena")
    md_lines.append("### Technical Project Report — TechWiz 7 Competition Submission")
    md_lines.append("")
    md_lines.append("**Team**: Data Minds 0.2  ")
    md_lines.append("**Team Members**:")
    md_lines.append("1. Abdulrahman Alsaqqaf")
    md_lines.append("2. Mohammed Babaqi")
    md_lines.append("3. Mohammed Bader")
    md_lines.append("4. Anas Alaroosi")
    md_lines.append("5. Malik Alshekeil")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("| Specification | DineIQ Analytics SRS v1.0 |")
    md_lines.append("|---|---|")
    md_lines.append("| **Architecture Framework** | Modular Monolith • Dual ML Tournament |")
    md_lines.append("| **Big Data Engine** | Apache Spark 4.2.0 • Snappy Parquet |")
    md_lines.append("| **Persistent Benchmark** | 1,302,220 Cleaned Records (11 Schemas) |")
    md_lines.append("| **Evaluation Agreement** | 63.48% Multi-Task Decision Match |")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Strip all HTML comments first
    html = re.sub(r'<!--.*?-->', '', html, flags=re.DOTALL)

    # Extract Table of Contents
    md_lines.append("## Table of Contents")
    md_lines.append("")
    toc_match = re.search(r'<div class="toc-page">(.*?)<div class="chapter-divider">', html, re.DOTALL)
    if toc_match:
        toc_content = toc_match.group(1)
        items = re.findall(r'<div class="toc-item(?:\s+part-header)?">(.*?)</div>', toc_content)
        for item in items:
            if "part-header" in item or "Part " in item:
                clean_part = re.sub(r'<[^>]+>', '', item).strip()
                clean_part = clean_part.replace('&amp;', '&')
                md_lines.append(f"\n### {clean_part}\n")
            else:
                num_match = re.search(r'<span class="toc-num">(\d+)</span><span>([^<]+)</span>', item)
                if num_match:
                    num, title = num_match.groups()
                    clean_title = title.replace('&amp;', '&').strip()
                    md_lines.append(f"- **Section {num}**: {clean_title}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")

    # Now parse the document chapters starting after TOC
    # Split by chapter dividers
    # <div class="chapter-divider">\s*<div class="chapter-number">(\d+)</div>\s*<div class="chapter-title">([^<]+)</div>\s*</div>
    chapters = re.split(r'<div class="chapter-divider">\s*<div class="chapter-number">(\d+)</div>\s*<div class="chapter-title">([^<]+)</div>\s*</div>', html)
    
    # chapters[0] is preamble/TOC
    # chapters[1] is num1, chapters[2] is title1, chapters[3] is body1, etc.
    i = 1
    while i < len(chapters):
        num = chapters[i].strip()
        title = chapters[i+1].strip().replace('&amp;', '&')
        body = chapters[i+2]
        i += 3
        
        # Strip closing-page from the last chapter body if present
        closing_match = re.search(r'<div class="closing-page">.*?</div>\s*</div>', body, re.DOTALL)
        if closing_match:
            body = body[:closing_match.start()]
            
        md_lines.append(f"## {num}. {title}")
        md_lines.append("")
        
        # Process the body into markdown blocks
        # 1. Alerts
        # Replace <div class="alert alert-{type}"><div class="alert-title">{title}</div>{content}</div>
        def alert_sub(m):
            atype = m.group(1).lower()
            atitle = m.group(2).replace('&amp;', '&').strip()
            acontent = m.group(3).strip()
            # Strip html tags from content
            clean_c = re.sub(r'<[^>]+>', '', acontent).strip()
            clean_c = clean_c.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<')
            
            tag = "NOTE"
            if "warning" in atype: tag = "WARNING"
            elif "risk" in atype or "danger" in atype: tag = "CAUTION"
            elif "important" in atype or "rule" in atype: tag = "IMPORTANT"
            elif "tip" in atype or "pass" in atype: tag = "TIP"
            
            return f"\n> [!{tag}]\n> **{atitle}**\n> {clean_c}\n"

        body = re.sub(r'<div class="alert alert-([a-zA-Z0-9_-]+)">\s*<div class="alert-title">([^<]+)</div>(.*?)</div>', alert_sub, body, flags=re.DOTALL)
        
        # 2. Figures:
        # <div class="figure-container">\s*<img src="([^"]+)" alt="([^"]+)"[^>]*>\s*<div class="figure-caption">([^<]+)</div>\s*</div>
        def fig_sub(m):
            src = m.group(1).strip()
            alt = m.group(2).strip()
            caption = m.group(3).replace('&amp;', '&').strip()
            return f"\n\n![{alt}]({src})\n\n*{caption}*\n\n"

        body = re.sub(r'<div class="figure-container">\s*<img src="([^"]+)" alt="([^"]+)"[^>]*>\s*<div class="figure-caption">([^<]+)</div>\s*</div>', fig_sub, body, flags=re.DOTALL)

        # 3. Tables:
        # Parse <table>...</table> followed by optional <div class="table-caption">...</div>
        def table_sub(m):
            t_content = m.group(1)
            caption_match = re.search(r'<div class="table-caption">([^<]+)</div>', body[m.end():m.end()+200])
            
            rows = re.findall(r'<tr[^>]*>(.*?)</tr>', t_content, re.DOTALL)
            md_table = []
            headers = []
            for r_idx, r in enumerate(rows):
                ths = re.findall(r'<th[^>]*>(.*?)</th>', r, re.DOTALL)
                tds = re.findall(r'<td[^>]*>(.*?)</td>', r, re.DOTALL)
                cols = ths if ths else tds
                clean_cols = []
                for c in cols:
                    cc = re.sub(r'<[^>]+>', '', c).strip()
                    cc = cc.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<').replace('&plusmn;', '±')
                    clean_cols.append(cc)
                
                if r_idx == 0:
                    headers = clean_cols
                    md_table.append("| " + " | ".join(clean_cols) + " |")
                    md_table.append("| " + " | ".join(["---"] * len(clean_cols)) + " |")
                else:
                    # Pad if mismatch
                    while len(clean_cols) < len(headers):
                        clean_cols.append("")
                    md_table.append("| " + " | ".join(clean_cols[:len(headers)]) + " |")
            
            res = "\n" + "\n".join(md_table) + "\n"
            if caption_match:
                cap = caption_match.group(1).replace('&amp;', '&').strip()
                res += f"*{cap}*\n"
            return res

        body = re.sub(r'<table[^>]*>(.*?)</table>(?:\s*<div class="table-caption">[^<]+</div>)?', table_sub, body, flags=re.DOTALL)

        # 4. Code blocks
        def pre_sub(m):
            code_content = m.group(1)
            clean_c = re.sub(r'<[^>]+>', '', code_content)
            clean_c = clean_c.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&').replace('&quot;', '"')
            return f"\n```\n{clean_c.strip()}\n```\n"

        body = re.sub(r'<pre(?: class="[^"]*")?><code>(.*?)</code></pre>', pre_sub, body, flags=re.DOTALL)

        # 5. Headings: h2, h3, h4
        body = re.sub(r'<h2[^>]*>(.*?)</h2>', lambda m: f"\n### {clean_text(re.sub(r'<[^>]+>', '', m.group(1))).replace('&amp;', '&')}\n", body)
        body = re.sub(r'<h3[^>]*>(.*?)</h3>', lambda m: f"\n#### {clean_text(re.sub(r'<[^>]+>', '', m.group(1))).replace('&amp;', '&')}\n", body)
        body = re.sub(r'<h4[^>]*>(.*?)</h4>', lambda m: f"\n##### {clean_text(re.sub(r'<[^>]+>', '', m.group(1))).replace('&amp;', '&')}\n", body)

        # 6. Lists
        def li_sub(m):
            content = m.group(1).strip()
            # replace <strong> with **
            content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', content)
            content = re.sub(r'<em>(.*?)</em>', r'*\1*', content)
            content = re.sub(r'<code>(.*?)</code>', r'`\1`', content)
            content = re.sub(r'<[^>]+>', '', content)
            content = content.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<').replace('&plusmn;', '±')
            return f"- {content}\n"

        body = re.sub(r'<li[^>]*>(.*?)</li>', li_sub, body, flags=re.DOTALL)
        body = re.sub(r'</?[ou]l[^>]*>', '\n', body)

        # 7. Paragraphs
        def p_sub(m):
            p_content = m.group(1).strip()
            p_content = re.sub(r'<strong>(.*?)</strong>', r'**\1**', p_content)
            p_content = re.sub(r'<em>(.*?)</em>', r'*\1*', p_content)
            p_content = re.sub(r'<code>(.*?)</code>', r'`\1`', p_content)
            p_content = re.sub(r'<a\s+href="([^"]+)"[^>]*>(.*?)</a>', r'[\2](\1)', p_content)
            p_content = re.sub(r'<span class="badge[^"]*">(.*?)</span>', r'[\1]', p_content)
            p_content = re.sub(r'<[^>]+>', '', p_content)
            p_content = p_content.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<').replace('&plusmn;', '±')
            clean_p = clean_text(p_content)
            if clean_p:
                return f"\n{clean_p}\n"
            return ""

        body = re.sub(r'<p[^>]*>(.*?)</p>', p_sub, body, flags=re.DOTALL)

        # Clean remaining HTML tags if any
        body = re.sub(r'<div[^>]*>', '\n', body)
        body = re.sub(r'</div>', '\n', body)
        body = re.sub(r'<span[^>]*>', '', body)
        body = re.sub(r'</span>', '', body)
        body = body.replace('&amp;', '&').replace('&gt;', '>').replace('&lt;', '<').replace('&plusmn;', '±')

        # Collapse excess empty lines
        body = re.sub(r'\n{3,}', '\n\n', body)
        md_lines.append(body.strip())
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")

    # Closing Section
    md_lines.append("## Submission & Verification Notice")
    md_lines.append("")
    md_lines.append("```")
    md_lines.append("================================================================================")
    md_lines.append("DINEIQ ANALYTICS — DATA SCIENCE INTELLIGENCE ARENA")
    md_lines.append("Official Technical Report for TechWiz 7 Competition Submission")
    md_lines.append("Team: DATA MINDS 0.2")
    md_lines.append("Members: Abdulrahman Alsaqqaf, Mohammed Babaqi, Mohammed Bader,")
    md_lines.append("         Anas Alaroosi, Malik Alshekeil")
    md_lines.append("Repository: datamindsye/DineIQ-Analytics")
    md_lines.append("Persistent Artifacts: 1,302,220 Cleaned Records | 12 Spark Analytical Marts")
    md_lines.append("                      4 ML Prediction Marts | 4 Head-to-Head Comparison Marts")
    md_lines.append("Status: All 32 SRS Domains, Dual ML Pipelines, Real BI Dashboards Verified")
    md_lines.append("================================================================================")
    md_lines.append("```")
    md_lines.append("")

    output_text = "\n".join(md_lines)
    with open(MD_PATH, "w", encoding="utf-8") as f:
        f.write(output_text)

    print(f"Markdown successfully built: {MD_PATH}")
    print(f"Size: {len(output_text)} characters, {len(md_lines)} lines")

if __name__ == "__main__":
    html_to_markdown()
