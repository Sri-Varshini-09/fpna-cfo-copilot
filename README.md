# 📊 FP&A CFO Copilot

An AI-powered assistant that answers financial questions directly from structured CSV data.  
CFOs can ask questions like:
- "What was June 2025 revenue vs budget?"
- "Show Gross Margin % trend for the last 3 months."
- "Break down Opex by category for June."
- "What is our cash runway right now?"

---

## 🚀 How to Run

```bash
# 1. Activate virtual environment
.\.fpna_env\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Streamlit app
streamlit run app.py

Then open http://localhost:8501 in your browser.

🧪 Run Tests
pytest -q


All core functions should pass ✅

📁 Project Structure
agent/          -> agent brain (intent + data tools)
fixtures/       -> CSV financial data
tests/          -> unit tests
app.py          -> Streamlit frontend