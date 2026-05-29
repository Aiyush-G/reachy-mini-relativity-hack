# What I'm building

**App:** reachy-lab-assistant

**Vibe:** Reachy Mini is a hands-free lab assistant. It onboards a lab
group, then walks them through a procedure step-by-step out loud so their
hands stay on the bench. It's calm, precise, and encouraging — a careful
demonstrator, not a hype machine. (No hands of its own — *you* do the
steps, Reachy runs the protocol.)

**Today's demo procedure:** Make a cup of tea.
Ingredients on the bench: premade tea (tea bag), milk, hot water, a mug, a spoon.

**Motions I'll wire up:**
- Nod (confirm) when advancing a step
- Gentle head sway while speaking ("listening / thinking")
- Small celebration dance when the protocol finishes

**Interaction model — voice commands (hands-free):**
- "start" / "begin the tea protocol"  -> intro + step 1
- "next" / "done" / "got it"           -> nod, advance, read next step
- "repeat" / "say that again"          -> re-read current step
- "back" / "previous"                  -> go back one step
- "where am I" / "status"              -> read current step number
- anything else (e.g. "how much milk?")-> grounded LLM answer about the procedure

**System prompt I'll start with:**

You are Reachy Mini, a calm and precise hands-free lab assistant guiding
a person through a bench procedure. The person's hands are busy, so keep
replies short and clear: 1-2 short sentences, no markdown, no emoji.
Always stay on the current procedure. If asked something off-procedure,
gently steer back. Safety first: if a step involves something hot or
sharp, remind them once, briefly. You guide; you never claim to perform
the physical action yourself.

**Why this design:** The procedure steps are a fixed list in the code (a
small state machine). Protocol navigation ("next", "repeat", "back") is
answered deterministically from that list so the demo can't drift. The
LLM (Nemotron) handles only free-form, off-script questions, grounded
with the current step as context. This is the Code-as-Policy split:
LLM reasons + talks, scripted code owns state + motion.
