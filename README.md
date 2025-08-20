# 📬 Bureaucracy Buddy — AI Web App (MVP)

**Bureaucracy Buddy** helps users understand and respond to official German letters.  
Paste text or upload a PDF → pick an AI action → edit the result → download as Word/PDF.  

---

## ✨ Features
- Plain-language summaries  
- Extract key details (deadlines, IDs, documents)  
- Draft polite German replies (editable, tone options)  
- Translate (EN ↔ DE) / Plain German (A2–B1)  
- Create actionable checklists  

---

## 🖼️ Screenshots

Home + Tasks  
<p align="center">
  <img src="https://github.com/AssadKhurshid/BureaucracyBuddy-MVP/blob/main/3_Uploading%20any%20doc.png" width="600" alt="Uploading Doc">
</p>


Editable Result + Downloads  
![Result](docs/images/result-editor.png)

---

## ✅ Why It’s Useful
- No login, accessible online (Streamlit/HF Spaces)  
- Clean, intuitive UI (Text/PDF input + sidebar settings)  
- Editable results before saving  
- Supports multiple LLM providers (OpenAI, Groq, Together, Hugging Face, Ollama)  
- Lightweight, proof-of-concept MVP  

---

## 🚀 Quickstart
```bash
# 1. Create virtual environment
python -m venv .venv
.venv\Scripts\activate   # Windows
source .venv/bin/activate  # macOS/Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run app
streamlit run app.py
