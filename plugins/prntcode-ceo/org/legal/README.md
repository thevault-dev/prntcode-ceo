# Legal · 🟢 live (Anthropic's legal plugin + PRNTCODE playbook)

**Owns:** contracts and intellectual property. That means Deepwear's manufacturing terms, collab agreements, commissions, NDAs, venue and pop-up contracts and hires, and protecting PRNTCODE's prints and name.

**How it runs:** on Anthropic's **legal** plugin, installed from Anthropic's marketplace so it keeps getting updates. The plugin isn't in this repo. What is here is PRNTCODE's playbook, [`legal.local.md`](legal.local.md), and the CEO router's hand-over: for any legal ask, the CEO reads the playbook and then hands over to the right `legal:` skill. The plugin's own defaults assume US law; the playbook is what makes it PRNTCODE's.

**Ask through the PRNTCODE agent.** The plugin finds `legal.local.md` by itself only in a Claude Code project's `.claude/` folder or a shared Cowork folder. In a claude.ai chat it gets the playbook only from the CEO, so say "PRNTCODE agent, review this contract", not `/legal:review-contract` on its own.

**Skills (live, from the plugin)**
- `legal:review-contract`: clause-by-clause review against the playbook, with redlines.
- `legal:triage-nda`: green, yellow or red on an incoming NDA.
- `legal:compliance-check`: regulations and approvals before acting.
- `legal:legal-risk-assessment`: severity and likelihood, and when to call a lawyer.
- `legal:signature-request`: pre-signature checklist and signing order.
- `legal:vendor-check`: what's signed and missing with a supplier or partner.
- `legal:legal-response`: replies to common legal requests.
- `legal:meeting-briefing` and `legal:brief`: prep and research.

**Planned (not built):** IP register (every print with its designer, date, files and owner under each contract), infringement watch, trademark watch, and redline and renewal tracking.

**Boundary:** it prepares and summarises. It doesn't replace a lawyer, and nothing goes to a counterparty or out for signature without Khaled's yes.
