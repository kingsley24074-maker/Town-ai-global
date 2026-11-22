import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from google import genai

app = FastAPI(title="Town AI Global Platform")
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class AskRequest(BaseModel):
    prompt: str
    mode: str = "Auto-Detect (Smart Router)"

@app.get("/", response_class=HTMLResponse)
def home():
    return """
    <!DOCTYPE html>
    <html>
    <head><title>Town AI — Global Multi-Skill Assistant, Scout, Auditor & Builder</title></head>
    <body style="font-family:sans-serif;max-width:860px;margin:40px auto;padding:0 16px;">
      <h1>Town AI</h1>
      <p>Multi-Skill Specialist Guidance, Artist & Sync Scout, Business/SaaS Auditor, and Website Builder.</p>
      <select id="mode">
        <option>Auto-Detect (Smart Router)</option>
        <option>UI/UX Design & Product Flows</option>
        <option>Copywriting & Conversion Messaging</option>
        <option>Paid Media & Performance Ads</option>
        <option>Video Editing, Retention & Short-Form</option>
        <option>Digital Marketing & Growth Specialist</option>
        <option>Programming, Software & Debugging</option>
        <option>Artist & Music Sync Scout + Audio Listener</option>
        <option>Business, SaaS, B2B & Creator Scout + Audit</option>
        <option>SEO, Content & Youth Food Strategy</option>
        <option>Website Builder</option>
        <option>Multi-AI Council</option>
      </select><br><br>
      <textarea id="prompt" rows="5" style="width:100%;" placeholder="Ask for specialist guidance in UI/UX, copywriting, paid media, video editing, coding, marketing, or scout/audit/build..."></textarea><br><br>
      <button onclick="sendPrompt()">Run Town AI</button>
      <pre id="out" style="white-space:pre-wrap;background:#f4f4f4;padding:16px;margin-top:20px;"></pre>
      <script>
        async function sendPrompt() {
          const out = document.getElementById("out");
          out.textContent = "Thinking...";
          const res = await fetch("/api/ask", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
              prompt: document.getElementById("prompt").value,
              mode: document.getElementById("mode").value
            })
          });
          const data = await res.json();
          out.textContent = data.reply;
        }
      </script>
    </body>
    </html>
    """

@app.post("/api/ask")
def ask_town_ai(req: AskRequest):
    resp = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=req.prompt,
        config={"system_instruction": f"You are Town AI, a multi-skill global specialist across UI/UX design, copywriting, paid media, video editing, digital marketing, programming, music A&R/sync, business/SaaS/B2B, SEO, and web building. Mode: {req.mode}. Deliver accurate, practical, human-like guidance."}
    )
    return {"reply": resp.text}
