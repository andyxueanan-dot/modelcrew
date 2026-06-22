# ModelCrew 🧮🤖

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/语言-简体中文-555?style=for-the-badge" alt="简体中文"></a>
  <a href="README_EN.md"><img src="https://img.shields.io/badge/Language-English-d9241c?style=for-the-badge" alt="English"></a>
</p>

> A **reusable** multi-agent crew for math-modeling contests: `Router` reads any problem →
> **summons the right specialists** (analyst / data / modeler / solver) → a skeptic ⭐`Critic`
> **interrogates every conclusion** adversarially → `Writer` produces the report.
> **Swap in a new problem and reuse it as-is — not a single line of the crew changes.**

Built for the **QoderWork CN Contest · Track 8 "Multi-Agent Orchestration Challenge"**.
First validated end-to-end on **2024 MCM Problem C (Tennis Momentum)**, then reused **with zero changes**
on **credit-card default prediction** (financial risk) to prove reusability.

---

## 🔁 The core: drop in a new problem and go (what Track 8 "orchestration" really tests)

ModelCrew's agents are defined by the **modeling *workflow***, not by **any single problem** — so the
framework stays untouched when the problem changes:

```
                          ┌──────────────────────────────────────────┐
  New problem + data ───▶ │  @ModelCrew suite (already installed)     │ ───▶  paper + anti-hallucination audit
                          │  Router→Analyst→Scout→Modeler→Solver      │
                          │         →⭐Critic→Writer (definition fixed)│
                          └──────────────────────────────────────────┘
```

**Reuse takes 3 steps — you never touch the crew definition:**

| Step | What you do | Change |
|---|---|---|
| 1️⃣ Drop in | Create `cases/<new>/`, add the problem statement + data | files only |
| 2️⃣ Summon | Tell `@ModelCrew` to "route this problem" | one sentence |
| 3️⃣ Run | Router classifies, summons specialists, Critic gates, Writer drafts | **0 lines of code** |

> **Why it's reusable**: the 7 roles abstract the *generic* modeling actions — read the problem,
> profile the data, pick a model, solve, interrogate, write — decoupled from any specific contest.
> Problem-agnostic ⟹ plug-and-play.
>
> ⚠️ **Honest note**: the diagram is the *full* 7-role roster, but the Router **tailors the actual
> dispatch by problem type** — not every problem summons all 7. Data-type (C) runs
> Analyst→Scout→Modeler→Solver→Critic→Writer; **optimization-type (B) auto-switches** to
> Analyst→Modeler→Solver→Critic→Writer (no heavy Scout). This "swap the chain by problem type" is
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

## ✨ Highlights

- **Reusable framework**: 7 AI roles packaged as an expert suite — swap the problem, reuse across contests (see 🔁 above).
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
python tools/check_frozen.py        # currently 17/17 consistent
```
> Each case's `artifacts/frozen_numbers.json` is the **single source of truth** for the paper's numbers;
> `check_frozen.py` auto-verifies "frozen == script output" and warns when `solve.py`/data changed —
> turning "anti-hallucination" from a manual Critic into an automatable gate (inspired by `math-modeling-skills`).

## 🛠 What software does it run on? (environment & portability)

**This entry was built and submitted on Qoder** (Track 8's requirement). But ModelCrew's "core" is **plain-Markdown role definitions + reference assets** (`agents/` + `references/`), **decoupled from any specific tool** — so it ports to other agentic tools; it is not Qoder-only.

| Tool | Works? | How |
|---|---|---|
| **Qoder** (native, tested) | ✅ easiest | 7 `SKILL.md` files = 7 skills → bundled into an expert suite; call skills with `/`, summon the crew with `@` |
| **Claude Code** (ported + verified) | ✅ verified | 7 subagents in [`.claude/agents/`](.claude/agents/), end-to-end smoke test passed ([log](.claude/agents/VERIFICATION.md)) |
| **Codex CLI** | ⚠️ possible, more manual | no "named-subagent suite" mechanism; put the roles in `AGENTS.md` and drive Router→…→Writer step by step via prompts |
| **Any LLM chat** | ⚠️ most bare-bones | use each `agents/*.md` as a system prompt and relay role by role manually |

> In short: **the submitted version is the Qoder one**; but since the core is just "roles + workflow + Critic gate" in Markdown, **it has been replicated and verified in Claude Code** (see [`.claude/agents/`](.claude/agents/): 7 subagents + format check + an end-to-end smoke test where the Critic correctly ruled "hot-hand exists" as ❌ on a mini problem). Qoder's value is packaging "skills / suites / subagents" into a one-click-install product you summon with a single `@`.

## Directory layout

```
qoder/
├── PLAN.md                  # master plan (framework / demos / timeline / checklist)
├── agents/                  # ★ 7-role source briefs (0_router … 6_writer, problem-agnostic)
├── skills/                  # 7 modelcrew-* skills (Qoder SKILL.md backups)
│   └── modelcrew-{router,analyst,scout,modeler,solver,critic,writer}/SKILL.md
├── references/              # 6 reference assets (model_catalog/anti_patterns/rubrics/
│                            #   feedback_layers/writing_templates/related_work)
├── cases/
│   ├── 2024_mcm_c_tennis/      # demo 1: tennis momentum (data-type / sports)
│   ├── credit_default_fintech/ # demo 2: credit-card default (data-type / finance)
│   └── 2024_logistics_siting/  # demo 3: emergency depot siting (optimization-type / OR)
├── tools/check_frozen.py    # number-traceability check (paper numbers ↔ script output, 24/24)
├── .claude/agents/          # 7 roles ported to Claude Code subagents (end-to-end verified)
└── submission/              # 实践文档.md + forum_post.md + 演示视频脚本.md
```

## Core ideas

- **Reusable**: agents are defined by the "modeling workflow", not "one problem"; a new problem just needs a new `cases/<x>/`.
- **Auto-summon**: the `Router` decides which specialists to call, and in what order, by problem type (continuous / discrete / data / optimization / environment / policy).
- ⭐**Anti-hallucination gate**: every conclusion must pass the `Critic`'s adversarial audit (randomness / causality / overfitting / extrapolation) before it ships; falsified ones roll back and redo — the step that turns "homework" into "real AI engineering".

---

<sub>By Andy (Xiamen University Malaysia · Data Science & Big Data Technology) · QoderWork CN Contest, Track 8 entry</sub>
