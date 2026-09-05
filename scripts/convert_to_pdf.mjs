import fs from 'fs';
import path from 'path';
import { marked } from 'marked';
import puppeteer from 'puppeteer';

import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const rootDir = path.resolve(__dirname, '..');

const mdPath = path.resolve(rootDir, 'docs', 'omnisales_detailed_report.md');
const pdfPath = path.resolve(rootDir, 'docs', 'OmniSales_Detailed_Report.pdf');
const mdContent = fs.readFileSync(mdPath, 'utf-8');

// Configure marked for proper heading IDs (for TOC links) and mermaid support
const renderer = new marked.Renderer();
renderer.heading = function ({ text, depth }) {
  const raw = typeof text === 'object' ? text.text || '' : text;
  const slug = raw.toLowerCase().replace(/[^\w\s-]/g, '').replace(/\s+/g, '-').replace(/-+/g, '-').trim();
  return `<h${depth} id="${slug}">${raw}</h${depth}>`;
};

// Convert ```mermaid blocks into <div class="mermaid"> so mermaid.js renders them
renderer.code = function ({ text, lang }) {
  if (lang === 'mermaid') {
    return `<div class="mermaid">${text}</div>`;
  }
  return `<pre><code class="language-${lang || ''}">${text}</code></pre>`;
};

marked.setOptions({ renderer, gfm: true, breaks: false });

const htmlBody = marked.parse(mdContent);

const fullHtml = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>OmniSales - Detailed Project Report</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<script>
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    themeVariables: {
      primaryColor: '#e8eaf6',
      primaryTextColor: '#1a1a2e',
      primaryBorderColor: '#3949ab',
      lineColor: '#5c6bc0',
      secondaryColor: '#f3e5f5',
      tertiaryColor: '#e8f5e9',
      fontSize: '13px'
    },
    flowchart: { curve: 'basis', padding: 20 }
  });
</script>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 10.5pt;
    line-height: 1.7;
    color: #1e293b;
    background: #ffffff;
    padding: 40px 50px;
  }

  h1 {
    font-size: 26pt;
    font-weight: 800;
    color: #0f172a;
    margin: 30px 0 10px 0;
    padding-bottom: 12px;
    border-bottom: 3px solid #3949ab;
    letter-spacing: -0.5px;
  }

  h2 {
    font-size: 16pt;
    font-weight: 700;
    color: #1e3a5f;
    margin: 35px 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #e2e8f0;
    page-break-after: avoid;
  }

  h3 {
    font-size: 12.5pt;
    font-weight: 600;
    color: #2e7d32;
    margin: 22px 0 8px 0;
    page-break-after: avoid;
  }

  h4 {
    font-size: 11pt;
    font-weight: 600;
    color: #b45309;
    margin: 16px 0 6px 0;
  }

  p { margin: 8px 0; }

  a {
    color: #3949ab;
    text-decoration: none;
  }

  strong { color: #0f172a; font-weight: 600; }
  em { color: #64748b; }

  hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 28px 0;
  }

  ul, ol {
    margin: 8px 0 8px 24px;
  }

  li {
    margin: 4px 0;
  }

  blockquote {
    border-left: 4px solid #3949ab;
    background: #f8fafc;
    padding: 12px 18px;
    margin: 12px 0;
    border-radius: 0 6px 6px 0;
    color: #475569;
    font-style: italic;
  }

  code {
    font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
    background: #f1f5f9;
    padding: 2px 6px;
    border-radius: 4px;
    font-size: 9pt;
    color: #3949ab;
  }

  pre {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    padding: 14px;
    overflow-x: auto;
    margin: 12px 0;
    font-size: 8.5pt;
    line-height: 1.5;
  }

  pre code {
    background: none;
    padding: 0;
    color: #334155;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 14px 0;
    font-size: 9.5pt;
    page-break-inside: avoid;
  }

  th {
    background: #1e3a5f;
    color: #ffffff;
    font-weight: 600;
    padding: 9px 12px;
    text-align: left;
    border: 1px solid #1e3a5f;
  }

  td {
    padding: 7px 12px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
  }

  tr:nth-child(even) { background: #f8fafc; }
  tr:nth-child(odd) { background: #ffffff; }

  .mermaid {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 20px;
    margin: 16px 0;
    text-align: center;
    page-break-inside: avoid;
  }

  h2 { page-break-before: auto; }
  table, pre, .mermaid { page-break-inside: avoid; }

  @media print {
    body { padding: 20px 30px; }
  }
</style>
</head>
<body>
${htmlBody}
</body>
</html>`;

// Write temp HTML
const htmlPath = path.resolve('_temp_report.html');
fs.writeFileSync(htmlPath, fullHtml, 'utf-8');

console.log('HTML generated. Launching Puppeteer...');

const browser = await puppeteer.launch({ headless: true, args: ['--no-sandbox'] });
const page = await browser.newPage();
await page.goto('file:///' + htmlPath.replace(/\\/g, '/'), { waitUntil: 'networkidle0', timeout: 60000 });

// Wait for mermaid to finish rendering
await page.waitForFunction(() => {
  const mermaidDivs = document.querySelectorAll('.mermaid');
  if (mermaidDivs.length === 0) return true;
  return Array.from(mermaidDivs).every(d => d.querySelector('svg'));
}, { timeout: 30000 });

console.log('Mermaid diagrams rendered. Generating PDF...');

await page.pdf({
  path: pdfPath,
  format: 'A4',
  printBackground: true,
  margin: { top: '20mm', bottom: '20mm', left: '15mm', right: '15mm' },
  displayHeaderFooter: true,
  headerTemplate: '<div></div>',
  footerTemplate: '<div style="width:100%;text-align:center;font-size:9px;color:#64748b;font-family:Inter,sans-serif;">OmniSales — Autonomous Revenue Department &nbsp;|&nbsp; Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>',
});

await browser.close();

// Cleanup temp HTML
fs.unlinkSync(htmlPath);

console.log(`PDF generated successfully: ${pdfPath}`);
