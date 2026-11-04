# Jacob Krzeminski — Selected Work

Four public case studies. Each one has its own architecture document,
evaluation document, and quality bar, and each one states what it does
not do as plainly as what it does.

The through-line is not "AI projects." It is evaluation and judgment
under uncertainty at scale, in settings where a confident wrong answer
costs something real: a $2.1T balance sheet, a 1.2M-resident municipal
service, a benefits determination, a law firm's privileged documents.

**What I have not done.** I have not trained a model, published a
research paper, worked on interpretability, or done machine learning
research. I have built the measurement apparatus and read the
literature; the modeling work is the part I am trying to get into.

**A note on authorship.** All four case-study repositories below were
built and written by me, with AI coding assistants, at a small company.
There is no team behind them and no co-author to check the reasoning
with. Where a repository says "we," it means me and the tools used to
build it. That is worth stating plainly, because a reader evaluating
this work should know they are reading one person's judgment rather than
a consensus.

**A note on attribution.** The City of Charlotte and
Charlotte-Mecklenburg Police Department appear in two of these
repositories because the problems are theirs and the published service
volumes come from the city's own records. Neither is involved in this
work, has reviewed it, or endorsed it. These are independent
prototypes about problems I have worked on, not products any government
has adopted.

---

## How to read these

Each repository follows the same structure, so a reader can go as deep
as they want or stop at the first screen:

| Section | What it answers |
|---|---|
| `README.md` | What this is, what we cut and why, quickstart, architecture, guardrails, known limitations, production roadmap, safety |
| `ARCHITECTURE.md` | The design in depth, with a diagram and the failure modes |
| `EVALUATION.md` | Every metric, its definition, its method, and which numbers are measured versus targeted |
| `QUALITY_BAR.md` | Every threshold this repo enforces, and why each one has the value it has |
| `scripts/gate.py` | One command that runs the checks and exits green or red |

**The "what we cut, and why" section is the point.** Each repository
lists the scope decisions it made and the reason for each. A reader who
sees deliberate boundaries with reasons can tell them apart from
oversights, and can tell which parts of the work I understand to be
provisional.

**Every repo ships a gate that is wired into CI.** Not a test suite
that happens to be green, but a set of checks with stated thresholds
that blocks the build. The interesting part is not that they pass, it
is which checks catch what: a public hotline number committed to a
public repo, a confirmation bypass, a stale standard, an inflated
claim.

---

## 1. FoodPath — NC FNS eligibility screener

**[github.com/JacobKrez/civic-reach-case-study](https://github.com/JacobKrez/civic-reach-case-study)**

A conversational screener that walks a North Carolina resident through
an initial Food and Nutrition Services (SNAP) eligibility screen: three
intake fields, a deterministic eligibility calculator, and a
grounded-in-cited-documents knowledge base.

**What I built.** A layered, explicit state machine. Keyword guardrails
run first and are deterministic and offline; a secondary LLM intent
classifier sits behind them as defense in depth and fails open. The
model is never asked to do arithmetic or to memorize eligibility rules.
It asks the next question and records explicitly supplied facts through
a single validated tool call, and a pure-Python calculator applies the
FY2027 federal income standards. Every final answer carries a
code-templated citation line the model cannot write. The same agent also
runs as a spoken (IVR) line, where the crisis rendering changes to
"hang up and call 911" because the caller is already holding a phone,
silence is handled as its own signal, and the spoken-confirmation
protocol treats a rejection as beating a confirmation.

**What I measured.** A red-team harness over a golden-transcript suite
and a property/fuzz suite, with per-category thresholds enforced in CI.
The crisis, injection, and false-positive categories are gated at 100%.
A quality-gate script runs ten checks and is wired into CI as the final
step, so a red gate blocks the build.

**What I found.** The failures worth finding were in the deterministic
layers, not the model. A caller who gives two incomes at once needs a
different operation than a caller who gives half of one, because
choosing between two complete figures cannot be done by concatenating
the question and the answer and re-parsing it. The confidence-guard
document records where a plausible-sounding wrong answer would have been
the most harmful output the tool had.

**What I did not do.** It does not determine eligibility, submit
applications, or contact any agency. There is no outbound path of any
kind. It is a proof of concept, and the case study says so on the first
paragraph of the README.

---

## 2. Charlotte 311 non-emergency call line

**[github.com/JacobKrez/charlotte-311-call-line](https://github.com/JacobKrez/charlotte-311-call-line)**

A voice agent for a municipal 311 line: a caller speaks, the agent
classifies the request, collects the fields needed to file it, reads
each field back for confirmation, and either files a case record or
hands off to a human.

**What I built.** A guardrail chain with a fixed, argued ordering:
emergency triage, then prompt-injection detection, then scope, then PII
redaction. Emergency triage runs first because a caller who reports an
active break-in on a non-emergency line matches both the emergency
detector and the injection detector, and answering that with an
injection refusal is the worst outcome the system can produce. The
ordering is asserted by a test rather than left to the order the
functions happen to be written in.

**What I measured.** A 50-case red-team corpus with per-category
thresholds: emergency, injection, and scope at 100%, false positives at
95%. Each case records *why it matters*, not just what it says, so the
corpus is a set of failure modes rather than a set of examples.

**What I found.** The central tension is that a rule-based emergency
detector has to match phrases, so it misses paraphrase. "He is currently
in my residence" does not match anything. That gap is measured and
stated rather than hidden, and it is the first item on the production
roadmap: a corpus written by someone who did not build the detector.

**What I did not do.** It has never handled a real call. It does not
dispatch 911, create a police report that reaches a dispatcher, or
connect to a case management system. The emergency path escalates
in-process to a human, and the README is explicit that a real
deployment needs a real telephony transfer, because that is where the
safety property lives or dies.

---

## 3. Charlotte municipal CRM — RFI response

**[github.com/JacobKrez/charlotte-municipal-crm](https://github.com/JacobKrez/charlotte-municipal-crm)**

The technical response to a competitive Request for Information from
the City of Charlotte for a CRM modernization serving 1.2 million
residents, roughly 925,000 annual 311 calls, and 28 connected
back-office systems.

**What I built.** A seven-layer architecture, a two-path voice design
where routine 311 calls are handled by AI and complex ones warm-transfer
to a human with full structured context, an AWS Bedrock hosting
decision driven by data residency and a no-training pledge rather than
by capability, and a NIST 800-53 Rev 5 control mapping delivered as a
mapping rather than a sentence.

**What I measured.** Deflection economics with the ROI math kept as a
method with clearly labeled inputs rather than as claims. The
architecture is evaluated against the city's confirmed FY25 volumes,
and the working assumptions for handle time and cost per call are
labeled as assumptions.

**What I found.** The 15-applications problem is the headline: every
311 interaction may require checking Cityworks, utility billing, code
enforcement, ArcGIS, permitting, and more, each in a separate
application. Two to three minutes of every call is navigation between
tabs, not conversation with a resident.

**What I did not do.** This was a procurement response, not a shipped
system. No pricing, no vendor comparison, and no confidential
question-and-answer content is published here, and the README lists
every cut and the reason for it. Coverage of the 232 applicable NIST
controls is 174, not 232, and the remaining 58 are categorized rather
than glossed.

---

## 4. Air-gapped legal AI

**[github.com/JacobKrez/sovereign-legal-ai](https://github.com/JacobKrez/sovereign-legal-ai)**

On-premise inference for law firms, running entirely inside a firm's own
network with no outbound internet path from the inference tier: a
dedicated network segment with no default gateway, a private switch
with no uplink, and physical isolation crossed only by removable media.

**What I built.** The deployment architecture and the ingestion path
from email attachment to a structured, auditable case record, with a
field-level grounding check that flags any field in a case record that
is not supported by a cited span of the source document. That check is
the core metric of the system: the rate of hallucinated fields.

**What I measured.** The metric definitions, measurement methods, and
thresholds for extraction fidelity, ingestion success rate, cluster
availability, and third-party audit artifact completeness, with an
explicit split between what is a target and what has been measured.

**What I found.** The interesting research question is not what the
system does but what air-gapped deployment *removes*. Once a model
runs in a privileged enclave with no egress, the ordinary external
safety levers, usage policies, production monitoring, staged rollouts,
are substantially reduced. The README states that the repository
contains no model training, no interpretability technique, and no novel
alignment method, and frames the deployment constraints as an open
problem rather than a safety claim.

**What I did not do.** No model training, no interpretability
technique, no novel alignment method, and no evaluated safety claim.
The air gap is not independently audited and the repository contains
no certification of it. Nothing about usage leaves the building, which
is the point of the design and also why the repository cannot report
real-world reliability numbers. The deployment architecture documented
is the target production topology; the software was developed and
demonstrated against a cloud-hosted model on synthetic material, and
no completed production rollout is claimed.

---

## The through-line

Across these four, the pattern is the same: build the thing, then find
the failure mode that matters, then measure it, then publish the
measurement *and* the gap.

Four things I would want a reviewer to check, because they are where
I think the work is weakest:

1. **Every red-team corpus here was written by the person who wrote the
   detector it tests.** A 100% pass rate is evidence of internal
   consistency, not generalization. The FoodPath and 311 repositories
   both say this in their evaluation documents, and both list
   independently-written corpora as the first item on their roadmaps.
2. **The 311 emergency detector matches phrases, not meaning.** It will
   miss paraphrase. I chose the phrase matcher over a semantic
   classifier because the outputs become public records, and a
   rule-based component that fails produces "no value extracted" rather
   than a plausible wrong value. That trade is real and it is not
   resolved.
3. **None of this has been evaluated against real traffic.** The
   shadow deployments that would produce a real escalation rate do not
   exist yet, and every threshold in these repositories is measured
   against a corpus rather than a call stream.
4. **The FoodPath screener had a stale-standards bug, and the gate
   caught it.** Its knowledge base carried FY2026 income limits whose
   provenance window expired 2026-09-30; FY2027 standards took effect
   2026-10-01, so for three weeks the screener was testing households
   against the prior year's thresholds, which can wrongly deny benefits
   to a household that qualifies. The repository's own provenance gate
   was failing the whole time. It was only noticed while adding the
   voice channel, because that work required the gate to be green in
   order to ship. The tables are now FY2027 and the gate is green, but
   the honest reading is that a passing gate is a necessary condition
   for correctness here and not a sufficient one: the gate fired late,
   and only because a new feature needed it.

---

## Background

I am an AI engineer and corporate treasury analyst at a large US bank,
and the founder of a small AI company. Two things from that split shape
how I build:

* **At work, the stake is a $2.1T balance sheet.** I was the only
  analyst on treasury's 12-person AI working group. The automation I
  built there replaced about 30 minutes of daily manual prep with a
  60-second pipeline that is in daily use. The lesson I carry forward
  is that the interesting problems there are judgment problems: what is
  the real risk, what evidence would change my mind, what do I do when
  the signal is noisy and I have to be wrong sometimes.
* **As a founder, the stake is that the thing has to work.** The four
  repositories above are all prototypes I built to understand a problem
  well enough to sell against it, and each one is scoped to a claim I
  can actually defend.

## Contact

- GitHub: [github.com/JacobKrez](https://github.com/JacobKrez)
- LinkedIn: [linkedin.com/in/jacobkrzeminskiua](https://linkedin.com/in/jacobkrzeminskiua)

## License

The repositories in this index are individually licensed. See each
repository's `LICENSE` file.
