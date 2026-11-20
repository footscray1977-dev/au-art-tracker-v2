import fs from 'fs';
import path from 'path';

export default function Home() {
  const reportPath = path.join(process.cwd(), 'public', 'report.html');
  let reportHtml = '';
  try {
    const raw = fs.readFileSync(reportPath, 'utf-8');
    const bodyMatch = raw.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
    reportHtml = bodyMatch ? bodyMatch[1] : raw;
  } catch {
    reportHtml = `
      <div style="padding:60px;font-family:-apple-system,sans-serif;text-align:center;">
        <h1 style="font-size:28px;color:#1C1B18;">Michael's Art Tracker</h1>
        <p style="color:#666;margin-top:12px;">No digest yet — the first sweep runs tonight at 3am AEST via GitHub Actions.</p>
        <p style="color:#999;font-size:13px;margin-top:8px;">946 artists · 339 overseas houses · daily at 03:00 Brisbane</p>
      </div>`;
  }

  return (
    <>
      <style>{`
        body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:#F7F5F0;color:#1C1B18;margin:40px}
        h1{margin-bottom:4px}.meta{color:#666;margin-bottom:24px}
        table{width:100%;border-collapse:collapse;background:#fff}
        th,td{padding:12px 14px;border-bottom:1px solid #E5E0D5;text-align:left;vertical-align:top}
        th{background:#1C1B18;color:#FAF7F2;font-size:12px;text-transform:uppercase;letter-spacing:.05em}
        a{color:#1B4D3E;font-weight:600;text-decoration:none}a:hover{text-decoration:underline}
      `}</style>
      <div dangerouslySetInnerHTML={{ __html: reportHtml }} />
    </>
  );
}
