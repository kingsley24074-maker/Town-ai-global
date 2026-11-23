import base64
import os
import re
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai
from google.genai import types

app = FastAPI(title="Town AI Global")

SYSTEM_PROMPT = """You are **Town AI**, a multi-skill global specialist across UI/UX, copywriting, paid media, video editing, digital marketing, programming, music A&R/sync licensing, business/SaaS/B2B auditing, SEO, and website building.

Rules:
- Adapt immediately to the selected mode (or auto-detect the user's intent if set to Auto-Detect).
- Deliver sharp, practical, human-like guidance with concrete recommendations.
- When in Artist & Sync Scout mode (or when an audio track is attached), evaluate hook strength, production clarity, vocal/instrumental balance, sync-licensing readiness (TV/film/ads/games), and exact pitch angles.
- When in Business/SaaS Auditor mode, audit positioning, conversion friction, pricing clarity, trust signals, and high-impact fixes.
- When in Website Builder mode, output a complete, responsive, single-file HTML document using Tailwind CSS CDN inside a ```html ... ``` code block so it can be rendered live in the preview frame.
"""

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Town AI — Multi-Skill Global Specialist</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
  <style>
    .markdown-body h1, .markdown-body h2, .markdown-body h3 { font-weight: 700; margin-top: 1rem; margin-bottom: 0.5rem; color: #f8fafc; }
    .markdown-body h1 { font-size: 1.35rem; }
    .markdown-body h2 { font-size: 1.15rem; }
    .markdown-body p { margin-bottom: 0.75rem; line-height: 1.65; }
    .markdown-body ul, .markdown-body ol { margin-left: 1.25rem; margin-bottom: 0.75rem; list-style-type: disc; }
    .markdown-body ol { list-style-type: decimal; }
    .markdown-body li { margin-bottom: 0.35rem; }
    .markdown-body strong { color: #38bdf8; font-weight: 600; }
    .markdown-body code { background: #0f172a; padding: 0.15rem 0.4rem; border-radius: 0.25rem; font-size: 0.875rem; color: #a5f3fc; }
    .markdown-body pre { background: #0f172a; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; margin-bottom: 0.75rem; border: 1px solid #1e293b; }
  </style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen font-sans antialiased">
  <div class="max-w-5xl mx-auto px-4 py-8">
    <!-- Header -->
    <header class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 pb-6 border-b border-slate-800">
      <div>
        <div class="flex items-center gap-2.5">
          <span class="inline-flex h-3 w-3 rounded-full bg-emerald-400 animate-pulse"></span>
          <h1 class="text-2xl sm:text-3xl font-extrabold tracking-tight text-white">Town AI</h1>
          <span class="text-xs font-semibold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-sky-500/10 text-sky-400 border border-sky-500/30">Global</span>
        </div>
        <p class="text-sm text-slate-400 mt-1">Multi-Skill Specialist Guidance, Artist &amp; Sync Scout, Business/SaaS Auditor, and Website Builder.</p>
      </div>
      <div class="text-xs text-slate-400 bg-slate-900 border border-slate-800 px-3 py-2 rounded-lg">
        Smart Router: <span class="text-emerald-400 font-medium">Online</span>
      </div>
    </header>

    <!-- Main Workspace -->
    <main class="mt-6 grid grid-cols-1 gap-6">
      <!-- Control Panel -->
      <section class="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label for="mode" class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Specialist Mode</label>
            <select id="mode" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white focus:outline-none focus:border-sky-500">
              <option value="Auto-Detect (Smart Router)">Auto-Detect (Smart Router)</option>
              <option value="Multi-Skill Specialist Guidance">Multi-Skill Specialist (UI/UX, Copy, Ads, Coding, SEO)</option>
              <option value="Artist & Sync Scout">Artist &amp; Sync Scout (Track Review &amp; Licensing)</option>
              <option value="Business/SaaS Auditor">Business / SaaS Auditor (Conversion &amp; Growth)</option>
              <option value="Website Builder">Website Builder (Live HTML + Tailwind Preview)</option>
            </select>
          </div>

          <div>
            <label for="targetUrl" class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Target URL (Optional — for Audits / Reference)</label>
            <input id="targetUrl" type="url" placeholder="https://example.com" class="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500" />
          </div>
        </div>

        <!-- Audio Track Upload -->
        <div class="mb-4">
          <label class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Upload Audio Track (Optional — MP3, WAV, M4A, OGG for A&amp;R / Sync Review)</label>
          <div class="flex flex-col sm:flex-row sm:items-center gap-3 bg-slate-950 border border-dashed border-slate-700 rounded-xl p-3">
            <input id="audioFile" type="file" accept=".mp3,.wav,.m4a,.ogg,audio/*" class="text-xs text-slate-300 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-sky-500/20 file:text-sky-300 hover:file:bg-sky-500/30 cursor-pointer" />
            <span id="audioStatus" class="text-xs text-slate-500">No track attached</span>
          </div>
        </div>

        <!-- Prompt Input -->
        <div class="mb-4">
          <label for="prompt" class="block text-xs font-semibold uppercase tracking-wider text-slate-400 mb-1.5">Your Request, Brief, or Question</label>
          <textarea id="prompt" rows="4" placeholder="Ask for specialist guidance in UI/UX, copywriting, paid media, video editing, coding, marketing, or scout/audit/build..." class="w-full bg-slate-950 border border-slate-700 rounded-xl p-3.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-sky-500"></textarea>
        </div>

        <div class="flex flex-wrap items-center justify-between gap-3">
          <button id="runBtn" onclick="runTownAI()" class="inline-flex items-center gap-2 bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-sm px-5 py-2.5 rounded-xl transition cursor-pointer shadow-lg shadow-sky-500/20">
            <span id="btnText">Run Town AI</span>
          </button>
          <button onclick="clearWorkspace()" class="text-xs text-slate-400 hover:text-slate-200 px-3 py-2 rounded-lg border border-slate-800 hover:border-slate-700 transition cursor-pointer">
            Clear
          </button>
        </div>
      </section>

      <!-- Output Workspace -->
      <section class="bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div class="flex items-center justify-between pb-3 mb-4 border-b border-slate-800">
          <span class="text-xs font-semibold uppercase tracking-wider text-slate-400">Specialist Output</span>
          <span id="activeBadge" class="text-xs text-sky-400 font-medium">Auto-Detect Ready</span>
        </div>

        <div id="output" class="markdown-body text-sm text-slate-200">
          <p>Got it. I'm <strong>Town AI</strong>, your multi-skill global specialist across UI/UX, copywriting, paid media, video editing, digital marketing, programming, music A&amp;R/sync, business/SaaS/B2B, SEO, and web building.</p>
          <p>My auto-detect router is engaged. Drop your question, attach an audio track for A&amp;R/sync scouting, paste a URL to audit, or request a full website build.</p>
        </div>
      </section>

      <!-- Live Website Preview Frame (Shown when Website HTML is generated) -->
      <section id="previewSection" class="hidden bg-slate-900/90 border border-slate-800 rounded-2xl p-5 shadow-xl">
        <div class="flex flex-wrap items-center justify-between gap-3 pb-3 mb-4 border-b border-slate-800">
          <div>
            <h2 class="text-sm font-bold text-white">Live Website Preview</h2>
            <p class="text-xs text-slate-400">Interactive single-file HTML + Tailwind render</p>
          </div>
          <button onclick="downloadWebsite()" class="bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold text-xs px-4 py-2 rounded-lg transition cursor-pointer">
            Download index.html
          </button>
        </div>
        <iframe id="previewFrame" class="w-full h-[540px] bg-white rounded-xl border border-slate-700"></iframe>
      </section>
    </main>
  </div>

  <script>
    let generatedHtml = "";

    document.getElementById("audioFile").addEventListener("change", (e) => {
      const file = e.target.files[0];
      document.getElementById("audioStatus").textContent = file
        ? `Attached: ${file.name} (${(file.size / (1024 * 1024)).toFixed(2)} MB)`
        : "No track attached";
    });

    function fileToBase64(file) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result.split(",")[1]);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    }

    function clearWorkspace() {
      document.getElementById("prompt").value = "";
      document.getElementById("targetUrl").value = "";
      document.getElementById("audioFile").value = "";
      document.getElementById("audioStatus").textContent = "No track attached";
      document.getElementById("previewSection").classList.add("hidden");
      generatedHtml = "";
    }

    function downloadWebsite() {
      if (!generatedHtml) return;
      const blob = new Blob([generatedHtml], { type: "text/html" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "town-ai-site.html";
      a.click();
      URL.revokeObjectURL(url);
    }

    async function runTownAI() {
      const mode = document.getElementById("mode").value;
      const prompt = document.getElementById("prompt").value.trim();
      const targetUrl = document.getElementById("targetUrl").value.trim();
      const audioInput = document.getElementById("audioFile");
      const audioFile = audioInput.files[0];

      if (!prompt && !audioFile && !targetUrl) {
        alert("Enter a prompt, paste a URL, or upload an audio track first.");
        return;
      }

      const btn = document.getElementById("runBtn");
      const btnText = document.getElementById("btnText");
      const output = document.getElementById("output");
      btn.disabled = true;
      btnText.textContent = "Thinking...";
      document.getElementById("activeBadge").textContent = mode;
      output.innerHTML = '<p class="text-slate-400 animate-pulse">Town AI is analyzing your request...</p>';

      try {
        let audioBase64 = null;
        let audioMime = null;
        if (audioFile) {
          if (audioFile.size > 15 * 1024 * 1024) {
            throw new Error("Audio file exceeds 15 MB limit. Please upload a shorter or compressed MP3/M4A.");
          }
          audioBase64 = await fileToBase64(audioFile);
          audioMime = audioFile.type || "audio/mpeg";
        }

        const res = await fetch("/api/run", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ mode, prompt, target_url: targetUrl, audio_base64: audioBase64, audio_mime: audioMime })
        });

        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Request failed.");

        output.innerHTML = marked.parse(data.reply);

        if (data.website_html) {
          generatedHtml = data.website_html;
          document.getElementById("previewFrame").srcdoc = generatedHtml;
          document.getElementById("previewSection").classList.remove("hidden");
        } else {
          document.getElementById("previewSection").classList.add("hidden");
        }
      } catch (err) {
        output.innerHTML = `<p class="text-rose-400 font-medium">Error: ${err.message}</p>`;
      } finally {
        btn.disabled = false;
        btnText.textContent = "Run Town AI";
      }
    }
  </script>
</body>
</html>
"""

class TownRequest(BaseModel):
    mode: str = "Auto-Detect (Smart Router)"
    prompt: str = ""
    target_url: str = ""
    audio_base64: str | None = None
    audio_mime: str | None = None

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_PAGE

@app.post("/api/run")
async def run_town_ai(req: TownRequest):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not set in environment variables.")

    client = genai.Client(api_key=api_key)

    user_message = f"Selected Mode: {req.mode}\n"
    if req.target_url:
        user_message += f"Target URL to Audit/Reference: {req.target_url}\n"
    user_message += f"Request:\n{req.prompt or 'Please review the attached track/URL according to the selected mode.'}"

    contents = [user_message]
    if req.audio_base64:
        audio_bytes = base64.b64decode(req.audio_base64)
        contents.append(
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type=req.audio_mime or "audio/mpeg",
            )
        )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )
        reply_text = response.text or "No response generated."
        html_match = re.search(r"```html\s*(.*?)\s*```", reply_text, re.DOTALL | re.IGNORECASE)
        website_html = html_match.group(1) if html_match else None
        return {"reply": reply_text, "website_html": website_html}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
