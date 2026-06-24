# ModelCrew 🧮🤖

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/语言-简体中文-555?style=for-the-badge" alt="简体中文"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/Language-English-d9241c?style=for-the-badge" alt="English"></a>
</p>

> A **reusable** multi-agent crew / full modeling copilot for math-modeling contests: `Router` reads any problem →
> **summons the right specialists** (analyst / data / modeler / solver) → a skeptic ⭐`Critic`
> **interrogates every conclusion** adversarially → `Writer` produces the report (**incl. a LaTeX submission**)
> → `Judge` **scores the whole paper like a referee**; with **4 human-in-the-loop checkpoints** along the way.
> **Swap in a new problem and reuse it as-is — not a single line of the crew changes.**

Built for the **QoderWork CN Contest · Track 8 "Multi-Agent Orchestration Challenge"**.
First validated end-to-end on **2024 MCM Problem C (Tennis Momentum)**, then reused **with zero changes**
on **credit-card default prediction** (financial risk) to prove reusability.

---

## 🔁 The core: drop in a new problem and go (what Track 8 "orchestration" really tests)

ModelCrew's agents are defined by the **modeling *workflow***, not by **any single problem** — so the
framework stays untouched when the problem changes:

```
                          ┌──────────────────────────────────────────────────┐
  New problem + data ───▶ │  @ModelCrew suite (already installed)             │ ───▶  LaTeX paper + audit + referee score
                          │  Router→Analyst→Scout→Modeler→Solver              │
                          │     →⭐Critic→Writer(+LaTeX)→Judge (definition fixed)│
                          │     ↑ 4 🛑 human checkpoints along the way          │
                          └──────────────────────────────────────────────────┘
```

**Reuse takes 3 steps — you never touch the crew definition:**

| Step | What you do | Change |
|---|---|---|
| 1️⃣ Drop in | Create `cases/<new>/`, add the problem statement + data | files only |
| 2️⃣ Summon | Tell `@ModelCrew` to "route this problem" | one sentence |
| 3️⃣ Run | Router classifies, summons specialists, Critic gates, Writer drafts | **0 lines of code** |

> **Why it's reusable**: the 8 roles abstract the *generic* modeling actions — read the problem,
> profile the data, pick a model, solve, interrogate, write, score — decoupled from any specific contest.
> Problem-agnostic ⟹ plug-and-play.
>
> ⚠️ **Honest note**: the diagram is the *full* 8-role roster, but the Router **tailors the actual
> dispatch by problem type** — not every problem summons all of them. Data-type (C) runs
> Analyst→Scout→Modeler→Solver→Critic→Writer→Judge; **optimization-type (B) auto-switches** to
> Analyst→Modeler→Solver→Critic→Writer→Judge (no heavy Scout). This "swap the chain by problem type" is
> already exercised on **both** a data-type and an optimization-type problem below (see `agents/0_router.md`).

### ✅ Reusability proven across three cases and two problem types

| Case | Type / Domain | Data | Crew changes | Highlight |
|---|---|---|---|---|
| `cases/2024_mcm_c_tennis/` | Data · sports/stats | 7,284 Wimbledon points | — | Critic ruled "momentum is real" ❌ (*hot-hand fallacy*) |
| `cases/credit_default_fintech/` | Data · **finance/risk** | 30k UCI credit-card rows | **0 lines** | Critic, as a "go-live review", vetoed deployment (fairness/compliance) |
| `cases/2024_logistics_siting/` | **Optimization** · OR/siting | 64-community depot siting | **0 lines** | Critic ruled "one search run = optimal" ❌ (local-optimum trap) |

> Same crew, from **tennis** → **bank credit risk** → **emergency-depot optimization**,
> **across data-type and optimization-type, not one line of the definition changed** — that's the hard evidence behind "reusable".

---

## 🚀 From "produce a report" to "a full modeling copilot"

ModelCrew now covers the whole pipeline — **get the problem → ramp up → model & solve → LaTeX paper → referee score** — with **4 human-decision checkpoints** in between:

| New capability | What it is | Landed evidence |
|---|---|---|
| 📝 **LaTeX submission** | Writer gains a LaTeX mode: `6_paper.md` (content truth) → fill template → `6_paper.tex`; MCM + CUMCM templates | tennis `6_paper.tex` **really compiled to a 6-page PDF via MiKTeX** (`cases/2024_mcm_c_tennis/artifacts/6_paper.pdf`) |
| ⚖️ **Judge (8th role)** | simulates a time-pressured referee, scores the whole paper against `rubrics.md` + estimated award (unofficial) + single highest-ROI fix; realizes the previously-dormant L3 panel | tennis `7_review.md`: total ≈75/100, est. H–M, weakest dim = innovation |
| 🛑 **4 human checkpoints** | pause after problem-reading / model-choice / a Critic ❌ / the judge score, to confirm or add judgment (can switch to `/grill-me`-style interrogation) | protocol `references/human_checkpoints.md`; sample `cases/.../checkpoints_log.md` |
| 🧰 **Weak-effect playbook** | when the main CI straddles the null, don't stop at "inconclusive": power/sample-size back-calc + TOST equivalence + E-value + decision-oriented closure turn "not significant" into decision value (**never overclaimed as significant**) | `references/inconclusive_playbook.md`; on the dispatch case it lifted the Judge **83→87** (below) |
| 🔢 **Auto prose-number check** | sinks "Critic hand-rolls a script to catch stale prose numbers" into a resident tool: verifies every cited number in the paper body against `frozen_numbers.json`'s `cited_in`, rounding-aware, zero false positives | `tools/check_paper_numbers.py`, **68/68** repo-wide; already caught + fixed a traceability gap in the siting case |
| 💡 **Innovation-boost list** | after the baseline, the Modeler must pass through "can it climb one tier?" (variant / combination / problem-operationalization + citable naming); the Judge scores innovation against it | `references/innovation_boost.md`; dispatch innovation dim 7→8.3 |

> **Judge ≠ Critic**: the Critic owns *is it correct* (✅/⚠️/❌ gate during the run); the Judge owns *how many points / what award* (terminal scoring).
> The checkpoints embody the positioning — ModelCrew is a **copilot**: the reusable workflow runs itself, the **key judgments stay with the human**.

> 🧪 **End-to-end self-run**: `cases/demo_dispatch_simpson/` (dispatch-policy eval with a planted Simpson's-paradox confounder) was run **start to finish by the upgraded 8 subagents themselves** — Router→Analyst→Scout→Modeler→Solver→Critic→Writer→Judge, for real: the Solver ran the **PoC smoke gate** (PASS) before solving three ways; ⭐the **Critic independently recomputed from the raw CSV, caught 3 stale numbers in the prose and triggered a fix** (`CORRECTION_audit.md`) while enforcing the "direction ≠ significance" wording; the CUMCM `6_paper.tex` **compiled to a PDF via xelatex**; the Judge scored **83/100** (est. upper 国二, unofficial).
>
> 🔁 **Then reused as the regression for a framework upgrade**: targeting the Judge's weakest points ("not significant → low decisiveness" + weak innovation), the gaps were sunk into framework capabilities (weak-effect playbook / prose-number checker / innovation-boost list), then re-run on this case — the Solver added **power back-calc (N=3412 needed for 80% power, vs 700) + TOST + E-value (1.566)**, the Writer added a **three-tier decision closure** in §8 (never crossing the "not significant" red line, confirmed by independent recompute in `5_audit.md §0.2`), the PDF recompiled to **14 pages**, and the Judge re-scored **83 → 87** (low 国一 / strong upper 国二, unofficial). `check_frozen` 35/35 + `check_paper_numbers` 68/68 all green. This proves both "the upgrade really raises the score" and "it runs, self-corrects, and self-improves."

---

## ✨ Highlights

- **Reusable framework**: 8 AI roles (incl. ⚖️ Judge) packaged as an expert suite — swap the problem, reuse across contests (see 🔁 above).
- ⭐**Anti-hallucination Critic**: adversarial per-conclusion audit + a three-way debate verdict — in the tennis demo it ruled "momentum is real" ❌ (the classic statistical *hot-hand fallacy*).
- **Real validation + reproducible**: 348 lines of Python, genuine statistical tests (Wald-Wolfowitz runs test / conditional permutation / logistic regression), one-command repro with `seed=42`.
- **Two rounds of cross-validation**: an independent AI + Codex review caught and fixed a statistical flaw (a no-op "server-adjusted" test); confirmed with a test that *truly* controls for serve — conclusion unchanged and stronger.
- 🏦 **Finance case (reusability proven)**: the same crew, **zero changes**, on **credit-card default prediction** (30k UCI credit-risk rows) — XGBoost AUC 0.782 / KS 0.422; the Critic, acting as a "bank model go-live review", vetoed direct deployment (fairness/compliance risk) and found that **removing sensitive attributes (sex/age) costs only ΔAUC 0.003** (compliance cost ≈ 0). See `cases/credit_default_fintech/`.

## ⚡ Reproduce in seconds (the demo numbers are real)

```bash
git clone https://github.com/andyxueanan-dot/modelcrew.git && cd modelcrew
pip install -r requirements.txt
# Finance case (credit-card default): writes AUC/KS to artifacts/results.json
cd cases/credit_default_fintech && python artifacts/solve.py && cd ../..
# Tennis case (momentum / hot-hand): writes runs test / permutation → solver_results.json
cd cases/2024_mcm_c_tennis   && python artifacts/solve.py
```

Both scripts fix `seed=42`; the printed numbers should match the JSON and the paper prose under each
`artifacts/` to the digit — the hard check behind this project's "anti-hallucination / reproducible" claim.

```bash
# Number traceability: every number cited in the papers traces back to a script output;
# flags STALE if a source script/data is newer than the results.
python tools/check_frozen.py        # frozen == script output, currently 35/35 consistent
python tools/check_paper_numbers.py # every prose citation == frozen value, currently 68/68 consistent
```
> Each case's `artifacts/frozen_numbers.json` is the **single source of truth** for the paper's numbers;
> `check_frozen.py` auto-verifies "frozen == script output" and warns when `solve.py`/data changed —
> turning "anti-hallucination" from a manual Critic into an automatable gate (inspired by `math-modeling-skills`).

## 🛠 What software does it run on? (environment & portability)

**This entry was built and submitted on Qoder** (Track 8's requirement). But ModelCrew's "core" is **plain-Markdown role definitions + reference assets** (`agents/` + `references/`), **decoupled from any specific tool** — so it ports to other agentic tools; it is not Qoder-only.

| Tool | Works? | How |
|---|---|---|
| **Qoder** (native, tested) | ✅ easiest | 8 `SKILL.md` files = 8 skills → bundled into an expert suite; call skills with `/`, summon the crew with `@` |
| **Claude Code** (ported + verified) | ✅ verified | 8 subagents in [`.claude/agents/`](.claude/agents/), end-to-end smoke test passed ([log](.claude/agents/VERIFICATION.md)) |
| **Codex CLI** | ⚠️ possible, more manual | no "named-subagent suite" mechanism; put the roles in `AGENTS.md` and drive Router→…→Writer step by step via prompts |
| **Any LLM chat** | ⚠️ most bare-bones | use each `agents/*.md` as a system prompt and relay role by role manually |

> In short: **the submitted version is the Qoder one**; but since the core is just "roles + workflow + Critic gate" in Markdown, **it has been replicated and verified in Claude Code** (see [`.claude/agents/`](.claude/agents/): 8 subagents + format check + an end-to-end smoke test where the Critic correctly ruled "hot-hand exists" as ❌ on a mini problem). Qoder's value is packaging "skills / suites / subagents" into a one-click-install product you summon with a single `@`.

## Directory layout

```
qoder/
├── PLAN.md                  # master plan (framework / demos / timeline / checklist)
├── agents/                  # ★ 8-role source briefs (0_router … 6_writer + 7_judge, problem-agnostic)
├── skills/                  # 8 modelcrew-* skills (Qoder SKILL.md backups)
│   └── modelcrew-{router,analyst,scout,modeler,solver,critic,writer,judge}/SKILL.md
├── templates/               # ★ LaTeX paper templates (MCM mcm_ / CUMCM cumcm_ + placeholder spec)
├── references/              # reference assets (model_catalog/anti_patterns/rubrics/feedback_layers/
│                            #   writing_templates/related_work/human_checkpoints/
│                            #   inconclusive_playbook ★weak-effect/innovation_boost ★innovation)
├── cases/
│   ├── 2024_mcm_c_tennis/      # demo 1: tennis momentum (data-type / sports) ★incl. 6_paper.tex/.pdf + 7_review.md
│   ├── credit_default_fintech/ # demo 2: credit-card default (data-type / finance)
│   ├── 2024_logistics_siting/  # demo 3: emergency depot siting (optimization-type / OR)
│   └── demo_dispatch_simpson/  # demo 4: dispatch-policy eval (data-type / Simpson) — 8 agents self-run + self-correct; weak-effect regression lifted Judge 83→87, .tex compiled to 14pp
├── tools/check_frozen.py        # number-traceability check (frozen ↔ script output, 35/35)
├── tools/check_paper_numbers.py # prose-number check (paper citations ↔ frozen, 68/68)
├── .claude/agents/          # 8 roles ported to Claude Code subagents (end-to-end verified)
└── submission/              # 实践文档.md + forum_post.md + 演示视频脚本.md
```

## Core ideas

- **Reusable**: agents are defined by the "modeling workflow", not "one problem"; a new problem just needs a new `cases/<x>/`.
- **Auto-summon**: the `Router` decides which specialists to call, and in what order, by problem type (continuous / discrete / data / optimization / environment / policy).
- ⭐**Anti-hallucination gate**: every conclusion must pass the `Critic`'s adversarial audit (randomness / causality / overfitting / extrapolation) before it ships; falsified ones roll back and redo — the step that turns "homework" into "real AI engineering".

---

<sub>By Andy (Xiamen University Malaysia · Data Science & Big Data Technology) · QoderWork CN Contest, Track 8 entry</sub>
