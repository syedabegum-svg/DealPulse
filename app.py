import os
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="DealPulse", page_icon="🧠", layout="wide")

# ---------- Styling ----------
st.markdown("""
<style>
:root { --ink:#e9eef8; --muted:#8f9bb3; }
.block-container {padding-top: 1.5rem; max-width: 1250px;}
.hero {padding: 1.2rem 0 1rem;}
.hero h1 {font-size: 2.55rem; margin-bottom: .15rem; letter-spacing:-1px;}
.hero p {color:#9aa7bd; font-size:1.05rem;}
.card {border:1px solid rgba(255,255,255,.10); border-radius:16px; padding:18px; background:rgba(255,255,255,.035);}
.metric {font-size:1.65rem; font-weight:700;}
.label {color:#8f9bb3; font-size:.8rem; text-transform:uppercase; letter-spacing:.08em;}
.memory {border-left:3px solid #6ea8fe; padding:8px 12px; margin:7px 0; background:rgba(110,168,254,.05); border-radius:0 10px 10px 0;}
.badge {display:inline-block; padding:4px 9px; border-radius:999px; background:rgba(110,168,254,.13); color:#a9c8ff; font-size:.75rem;}
.small {color:#8f9bb3; font-size:.88rem;}
</style>
""", unsafe_allow_html=True)

# ---------- Memory service ----------
class MemoryService:
    def __init__(self):
        self.mode = "Demo mode"
        self.client = None
        self.bank_id = os.getenv("HINDSIGHT_BANK_ID", "dealpulse-demo")
        base_url = os.getenv("HINDSIGHT_BASE_URL", "https://api.hindsight.vectorize.io")
        api_key = os.getenv("HINDSIGHT_API_KEY", "")
        if api_key:
            try:
                from hindsight_client import Hindsight
                self.client = Hindsight(base_url=base_url, api_key=api_key, timeout=30)
                self.mode = "Hindsight Cloud"
                try:
                    self.client.create_bank(bank_id=self.bank_id, name="DealPulse")
                except Exception:
                    pass
            except Exception as e:
                self.mode = f"Fallback ({type(e).__name__})"

        if "local_memories" not in st.session_state:
            st.session_state.local_memories = []

    def retain(self, content, context="Deal interaction"):
        if self.client:
            try:
                self.client.retain(
                    bank_id=self.bank_id,
                    content=content,
                    context=context,
                    timestamp=datetime.now()
                )
                return True
            except Exception:
                pass
        st.session_state.local_memories.append({
            "text": content, "type": "experience", "context": context,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        return True

    def recall(self, query):
        if self.client:
            try:
                result = self.client.recall(
                    bank_id=self.bank_id, query=query, max_tokens=3000, budget="mid"
                )
                return [{"text": x.text, "type": x.type, "context": getattr(x, "context", "")}
                        for x in result.results]
            except Exception:
                pass
        # Lightweight local fallback for demos before keys are configured.
        words = {w.lower() for w in query.split() if len(w) > 3}
        scored = []
        for m in st.session_state.local_memories:
            score = sum(w in m["text"].lower() for w in words)
            if score:
                scored.append((score, m))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored[:8]]

    def reflect(self, query, context=""):
        if self.client:
            try:
                result = self.client.reflect(
                    bank_id=self.bank_id,
                    query=query,
                    context=context,
                    budget="mid"
                )
                return result.text
            except Exception:
                pass
        memories = self.recall(query)
        return local_answer(query, memories)

memory = MemoryService()

# ---------- LLM ----------
def groq_answer(query, memories):
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        return local_answer(query, memories)
    try:
        from groq import Groq
        client = Groq(api_key=key)
        memory_text = "\n".join(
            f"- {m['text']}" for m in memories
        ) or "- No relevant prior memories found."
        system = """You are DealPulse, a concise B2B deal-intelligence agent.
Use the supplied deal memories as evidence. Never invent facts. Clearly distinguish
known history from recommendations. Give practical, salesperson-friendly answers.
When preparing a call, structure: Situation, Known concerns, Previous commitments,
Recommended approach, Questions to ask."""
        res = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            messages=[
                {"role":"system","content":system},
                {"role":"user","content":f"DEAL MEMORIES:\n{memory_text}\n\nQUESTION:\n{query}"}
            ],
            temperature=0.25,
            max_tokens=800,
        )
        return res.choices[0].message.content
    except Exception as e:
        return local_answer(query, memories) + f"\n\n*LLM fallback: {type(e).__name__}*"

def local_answer(query, memories):
    text = " ".join(m["text"] for m in memories)
    q = query.lower()
    if "prepare" in q or "call" in q:
        return f"""### Call Brief

**Situation**
This brief is grounded in {len(memories)} recalled deal memories.

**Known concerns**
{extract_points(text, ["price", "pricing", "analytics", "roi", "competitor", "budget", "security"])}

**Previous commitments**
{extract_points(text, ["promise", "send", "follow", "comparison", "demo"])}

**Recommended approach**
Lead with the customer's previously stated concern, confirm whether it is still blocking the deal, then connect the proposed next step to a measurable business outcome.

**Questions to ask**
- Has the main blocker changed since our last conversation?
- What evidence would make the decision easier?
- Who else needs to be comfortable before moving forward?"""
    return f"""I found **{len(memories)} relevant memories**.

{chr(10).join("• " + m["text"] for m in memories[:6]) if memories else "No matching memories yet. Add an interaction first."}

**DealPulse recommendation:** Use these historical signals as context, then confirm anything that may have changed."""

def extract_points(text, keywords):
    hits = []
    for sentence in text.replace("\n", " ").split("."):
        if any(k in sentence.lower() for k in keywords):
            s = sentence.strip()
            if s and s not in hits:
                hits.append(s)
    return "\n".join(f"- {x}" for x in hits[:4]) or "- No explicit item found in recalled memories."

def seed_demo():
    if st.session_state.get("seeded"):
        return
    demo = [
        ("2026-09-10", "Discovery call with Acme Technologies. Sarah Khan, VP Operations, said they want to automate invoice reconciliation and reduce manual processing."),
        ("2026-09-14", "Pricing discussion with Acme Technologies. Sarah said the proposed ₹8,00,000 annual price feels expensive and asked whether quarterly billing is possible."),
        ("2026-09-18", "Product call with Acme Technologies. Sarah said their current vendor has stronger analytics dashboards. Competitor X was mentioned twice."),
        ("2026-09-21", "Follow-up with Acme Technologies. We promised to send an ROI comparison showing how automation could pay back within six months."),
        ("2026-09-24", "Email from Acme Technologies. They are interested but need evidence of measurable ROI before procurement will approve the purchase."),
    ]
    for date, content in demo:
        memory.retain(content, context=f"Acme deal interaction — {date}")
    st.session_state.seeded = True

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## 🧠 DealPulse")
    st.caption("Memory-powered deal intelligence")
    st.divider()
    st.markdown(f"**Memory:** `{memory.mode}`")
    st.markdown(f"**Bank:** `{memory.bank_id}`")
    if st.button("Load demo deal", use_container_width=True):
        seed_demo()
        st.success("Acme demo memories loaded.")
    if st.button("Clear local demo memory", use_container_width=True):
        st.session_state.local_memories = []
        st.session_state.seeded = False
        st.rerun()

# ---------- Header ----------
st.markdown('<div class="hero"><h1>🧠 DealPulse</h1><p>Your sales team\'s memory — learning from every interaction.</p></div>', unsafe_allow_html=True)

# ---------- Deal summary ----------
c1, c2, c3, c4 = st.columns(4)
for col, label, value in [
    (c1, "Account", "Acme Technologies"),
    (c2, "Deal value", "₹8,00,000"),
    (c3, "Stage", "Negotiation"),
    (c4, "Memory", memory.mode),
]:
    with col:
        st.markdown(f'<div class="card"><div class="label">{label}</div><div class="metric">{value}</div></div>', unsafe_allow_html=True)

st.write("")

tab_chat, tab_memory, tab_add, tab_demo = st.tabs(["💬 Deal Copilot", "🧠 Memory", "➕ Add interaction", "🎬 Demo story"])

with tab_chat:
    st.markdown("### Ask about Acme")
    st.caption("Try: **Prepare me for today's Acme call** · **What did I promise them?** · **What are their biggest objections?**")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
    prompt = st.chat_input("Ask DealPulse about this deal...")
    if prompt:
        st.session_state.messages.append({"role":"user","content":prompt})
        memories = memory.recall(prompt + " Acme Technologies deal history")
        answer = memory.reflect(prompt, context="Sales call preparation for Acme Technologies")
        # If Hindsight is connected, reflect is the primary answer. If local, use Groq if available.
        if memory.client is None and os.getenv("GROQ_API_KEY"):
            answer = groq_answer(prompt, memories)
        st.session_state.messages.append({"role":"assistant","content":answer})
        memory.retain(f"Sales rep asked: {prompt}\nDealPulse answered: {answer}", context="DealPulse interaction")
        st.rerun()

with tab_memory:
    st.markdown("### What DealPulse remembers")
    memories = memory.recall("Acme Technologies pricing objections competitor analytics ROI commitments previous conversations")
    if memories:
        for m in memories:
            st.markdown(f'<div class="memory"><span class="badge">{m.get("type","memory")}</span><br>{m["text"]}<div class="small">{m.get("context","")}</div></div>', unsafe_allow_html=True)
    else:
        st.info("No memories yet. Load the demo deal or add an interaction.")

with tab_add:
    st.markdown("### Record a new interaction")
    with st.form("interaction"):
        kind = st.selectbox("Interaction type", ["Call", "Email", "Meeting", "Objection", "Commitment", "Outcome"])
        notes = st.text_area("What happened?", height=160, placeholder="Example: Acme said they will proceed if we can demonstrate six-month ROI.")
        submitted = st.form_submit_button("Retain in DealPulse memory", type="primary")
    if submitted:
        if not notes.strip():
            st.warning("Add some notes first.")
        else:
            memory.retain(f"Acme Technologies — {kind}: {notes}", context=f"Deal interaction ({kind})")
            st.success("Interaction retained. The agent can use it in future answers.")

with tab_demo:
    st.markdown("### 🎬 60-second judge demo")
    st.markdown("""
**1. Start with a blank-looking deal**  
Say: *“A normal chatbot doesn't know what happened before.”*

**2. Load the Acme deal**  
Five interactions become persistent memories: pricing, competitor, analytics, ROI and a promised follow-up.

**3. Ask:**  
> **“Prepare me for today's Acme call.”**

**4. Add a new outcome:**  
> *“Acme will only proceed if we can prove six-month ROI.”*

**5. Ask the same question again.**  
The answer now incorporates the new signal alongside the older deal history.

**6. Close with:**  
> **“DealPulse doesn't just store the conversation. It gets more useful as the relationship develops.”**
""")
    st.info("For the final demo, use Hindsight Cloud so the memory layer is visibly real rather than only local fallback storage.")

st.divider()
st.caption("DealPulse • HackWithHyderabad 3.0 • Built around Hindsight retain → recall → reflect")
