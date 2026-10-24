<p align="center">
  <img src="https://raw.githubusercontent.com/manaplatform/mana-agent/refs/heads/main/logo.png" alt="Mana-Agent logo" width="100%" />
</p>

<h1 align="center">Mana-Agent + GPT-6-Luna</h1>

<p align="center">
  <strong>SWE-bench Verified — Evaluation Submission</strong><br />
  Open-source agent orchestration for real-world software engineering tasks.
</p>

<p align="center">
  <a href="https://github.com/manaplatform/mana-agent">Source Code</a> ·
  <a href="https://github.com/SWE-bench/SWE-bench">SWE-bench</a> ·
  <a href="https://github.com/SWE-bench/experiments">Leaderboard Submissions</a>
</p>

> **Submission status: LOCAL EVALUATION — NOT LEADERBOARD-ELIGIBLE AS RUN.** Patch-matched local Docker evaluations show **371/500 (74.20%) resolved**. However, an audit of 500 recorded agent prompts found **335 containing a `Hints:` section**, and the referenced runner source shows that this section contains SWE-bench `hints_text`. Official SWE-bench Verified rules prohibit use of these hints. Some initially empty predictions were also regenerated. These figures document a **noncompliant historical experiment**, not a valid leaderboard submission or independently verified score. A new, clean evaluation without prohibited hints and with a compliant, documented attempt policy would be needed for an eligible submission.

## Overview

**Mana-Agent** is an open-source, Python-based AI-agent orchestration platform developed by **ManaPlatform**. It is designed to carry software-engineering work beyond a single model response: investigate repositories, plan changes, coordinate tool execution, apply code modifications, and inspect verification results.

This submission evaluates Mana-Agent using the **GPT-6-Luna** model configuration on the **500-instance SWE-bench Verified** benchmark. The underlying model is provided by OpenAI; Mana-Agent is the agent system that coordinates the coding workflow.

- **Agent:** Mana-Agent
- **Agent organization:** ManaPlatform
- **Model:** GPT-6-Luna (OpenAI)
- **Benchmark:** SWE-bench Verified
- **Public agent source:** https://github.com/manaplatform/mana-agent
- **Open-source agent:** Yes (MIT-licensed)
- **Open-weight model:** No
- **Evaluation period:** October 2026. Precise start/end timestamps must be confirmed from the retained local run logs.
- **Repository revision referenced by the evaluation draft:** [`01d44970daa9d732d58168d2805fa2e92c434f65`](https://github.com/manaplatform/mana-agent/commit/01d44970daa9d732d58168d2805fa2e92c434f65) (commit exists; confirm it was the exact checkout for each generated prediction).
- **Technical report:** Not yet published; a substantial public technical report or preprint is required for a new leaderboard submission.

## System Description

Mana-Agent's public architecture includes the following components:

| Component | Role |
| --- | --- |
| Autonomous execution loop | Advances tasks through investigation, execution, inspection, and subsequent actions. |
| TaskBoard | Tracks tasks, dependencies, status, and verification evidence in support of the loop. |
| Execution supervisor | Coordinates controlled execution, progress tracking, and recovery for multi-step workflows. |
| Coding and tool integrations | Inspect repositories, edit code, invoke command-line tools, and run tests using configured execution backends. |
| Context and memory mechanisms | Maintain relevant workflow context and learned operational lessons where enabled. |
| Verification workflow | Relates agent-produced patches to actual test results rather than assuming a successful run. |

**Benchmark-specific configuration, confirmed from the repository revision above:**

- **Runner:** `scripts/swe_bench/runner.py` generates predictions from `princeton-nlp/SWE-bench_Verified` (test split by default). The *evaluation harness* uses `SWE-bench/SWE-bench_Verified`; these dataset identifiers are not interchangeable in the harness.
- **Model and provider:** The submission identifies `openai` / `gpt-6-luna`. Actual per-instance model/provider settings should be verified from the saved `mana_cmd.txt` / `result.json` records.
- **Execution:** A per-instance isolated Git worktree and isolated `MANA_HOME`; the agent runs via non-interactive `mana-agent chat --no-tui --full-auto --no-auto-index-missing --no-coding-memory --auto-continue --execution-profile full-auto --auto-execute-max-passes 10`. Agent output and prompts are saved per instance.
- **Runner defaults, not verified run-specific limits:** 600-second wall-clock timeout (override `--timeout 0` means no runner wall-clock limit); maximum prompt length of 48,000 characters; exclusion of test-file hunks from generated patches. If actual CLI/environment overrides differed, report those instead.
- **Coding backend and permitted tools:** The runner invokes Mana-Agent's configured coding backend; the particular backend, tool permissions, token budgets, and web-access policy actually used in this evaluation still require confirmation from the saved configuration and trajectories. Never publish credentials.
- **Benchmark-integrity finding:** At the referenced revision, `build_prompt()` appends `hints_text` when nonempty. The local prompt audit found the resulting `Hints:` section in **335 of 500** stored prompt files. The official submission checklist prohibits use of the dataset hints; these results must not be described as checklist-compliant. See **Benchmark Integrity** below.

## Benchmark and Evaluation

[SWE-bench Verified](https://www.swebench.com/) contains 500 software-engineering issues with curated evaluation tests. For each instance, the agent receives a repository issue and is expected to produce a source-code patch. The official evaluation harness applies that patch to the instance environment and runs the corresponding tests inside Docker.

### Prediction generation

Predictions are recorded as JSONL entries including:

```json
{
  "instance_id": "<SWE-bench instance ID>",
  "model_name_or_path": "mana-agent__gpt-6-luna",
  "model_patch": "<unified diff produced by Mana-Agent>"
}
```

**Submission predictions:** `all_preds.jsonl` in the published artifact repository. During local preparation, the prediction files were named `predictions.jsonl` and `remaining_predictions.jsonl`; the latter contains regenerated predictions for selected previously empty-patch tasks.

### Evaluation environment

- **Dataset:** `SWE-bench/SWE-bench_Verified`, `test` split.
- **Harness:** Official Python `swebench.harness.run_evaluation` runner.
- **Execution:** Docker-based SWE-bench evaluation containers, including AMD64 images where necessary.
- **Recorded evidence:** Per-instance patches, official evaluation reports, and test outputs.
- **Local audit environment (not necessarily the original grading environment):** Darwin 27.0.0, arm64; Python 3.14.7; Docker 29.9.2 (build a82e528). The audit Python environment did not have SWE-bench installed. Original evaluation used per-instance `--max_workers 1`; confirm original package versions and actual run settings from grading records.

A typical *per-instance* local validation invocation is:

```bash
python -m swebench.harness.run_evaluation \
  --dataset_name SWE-bench/SWE-bench_Verified \
  --predictions_path /path/to/single-instance-prediction.jsonl \
  --instance_ids <instance_id> \
  --max_workers 1 \
  --run_id <run_id>
```

The submission consolidates evidence from multiple independently executed instance evaluations. **Each published report must correspond to the exact final `model_patch` for that instance**; the existence of a test log by itself is not proof that the published patch was evaluated.

### Results

Results below are calculated from the locally consolidated final `predictions.jsonl` and **exactly matching** official per-instance patch/test/report evidence as reported by the 2026-10-24 local audit. They are not a union of successes from historical attempts. **Because prohibited hints were present in recorded agent prompts, 74.20% is an internal research result, not an eligible SWE-bench Verified leaderboard result.** Results must be recalculated if the final published predictions differ.

| Metric | Final result |
| --- | ---: |
| Total benchmark instances | 500 |
| Instances with final predictions | 500 |
| Instances with matching official evaluation evidence | 498 |
| Resolved instances | 371 |
| Unresolved instances | 127 |
| Empty patches | 2 |
| Missing or unevaluated instances | 2 |
| Resolved / 500 | 371 / 500 (74.20%) |

**Official `swebench submit package` summary (required in the leaderboard README/PR description):**

```text
Pending: paste the original, unmodified output of `swebench submit package` after producing the actual final package. Do not substitute an estimate.
```

The local audit examined 498 report files; found **zero mismatched patches, conflicting same-patch reports, invalid reports, or missing test outputs for matching reports**. The two final empty-patch instances without matching grading reports are `django__django-16315` and `scikit-learn__scikit-learn-25973`, counted as unresolved for the 500-instance score. The local file `mana-agent__gpt-6-luna.json` is only a summary and does not replace the official report/test artifacts.

## Attempt Policy and Disclosure

**This experiment includes regenerated patches for some tasks that initially produced an empty patch.** The initial predictions and subsequent rerun predictions were kept in separate files during local development before consolidation.

The submission is **not described as an untouched single-attempt pass@1 experiment**. The current metadata declares `tags.system.attempts: "2+"` pending a complete audit of the actual attempt counts and selection process.

Before requesting leaderboard inclusion, the authors must document and verify:

1. Exactly which instance IDs were attempted more than once and the number of attempts for each.
2. What triggered each rerun and whether any official evaluation result was used in the decision.
3. How a final patch was selected **without selecting based on SWE-bench evaluation results**.
4. Whether every attempt is represented in the published execution trajectories.
5. Whether the resulting procedure qualifies under the current SWE-bench rules for multi-attempt submissions.

**Eligibility warning:** The official checklist disallows selecting patches using SWE-bench evaluation feedback. If such feedback influenced patch selection, the result must not be presented as a compliant best@k or pass@1 leaderboard score. In addition, this run is already noncompliant due to the recorded inclusion of prohibited hints. See the [official submission checklist](https://github.com/SWE-bench/experiments/blob/main/checklist.md).

## Benchmark Integrity and Reproducibility

### Recorded prompt audit: prohibited benchmark hints

On October 24, 2026, the local auditor scanned the saved Mana-Agent prompts using `--agent-logs ../mana-agent/.swe-bench/logs` and reported:

```text
Prompt files scanned:             500
Files containing a Hints section: 335
```

The runner at the referenced commit constructs prompts using `instance.get("hints_text")` and adds a `Hints:` section when this field is nonempty. Thus, **335 recorded prompts contained information drawn from the prohibited SWE-bench `hints_text` field**. The current official submission checklist says agents must not use the dataset hints. We do not claim that the model relied on the information for any particular patch, but its presence in inputs means **this historical run does not meet the benchmark-input restriction**.

**Do not publish this experiment as an official pass@1, best@k, or checklist-compliant SWE-bench Verified result.** Altering logs, deleting `Hints:` sections after inference, changing metadata, or patching the runner after the fact cannot fix the historical experiment. To prepare a compliant new submission, first remove the hints from the actual prompt construction, audit tool access to prevent solution lookup, establish a compliant attempt-selection rule, regenerate predictions from scratch, and grade those *new* predictions. Preserve the historical result separately with its limitations disclosed.

### Other integrity requirements

The full technical report should also establish whether the agent could browse the web or external code sources, whether answer lookup was blocked or audited, and whether official `PASS_TO_PASS` / `FAIL_TO_PASS` test knowledge was excluded from all model prompts and decision policies.

| Checklist item | Status for this historical experiment |
| --- | --- |
| One attempt per instance (`pass@1`) | **No** — some initially empty predictions were regenerated |
| `hints_text` excluded from prompts | **No** — `Hints:` appears in **335/500** recorded prompts |
| Official test knowledge excluded | Not established; requires input and retry-selection audit |
| External solution lookup prevented or audited | Not established; inspect allowed tools and execution traces |
| Final predictions match retained evaluation reports | **Yes for 498 instances**; 2 final empty patches have no matching report |
| Every attempt and selection mechanism reflected in trajectories | Not established; rerun trace completeness must be checked |
| Artifacts publicly accessible | Not established; publication is pending |

## Public Artifacts

The published benchmark-artifact repository should contain:

```text
mana-agent-swebench-verified/
├── all_preds.jsonl
├── logs/
│   └── <instance_id>/
│       ├── patch.diff
│       ├── report.json
│       └── test_output.txt.gz
└── trajs/
    └── <instance_id>.txt
```

- **Artifacts repository:** Not yet published. Proposed repository: `manaplatform/mana-agent-swebench-verified` (create it and publish the artifacts before using its URL in metadata).
- **Evaluation logs:** Not yet public; after publishing, link to `<artifact-repo>/tree/main/logs`.
- **Agent trajectories:** Not yet public; after publishing, link to `<artifact-repo>/tree/main/trajs`.

The `trajs/` files should describe genuine execution activity captured during inference. Concatenated prompt, stdout, summary, and result logs can help document an attempt, but must not be represented as containing model/tool events that were never logged. Review all files for API keys, access tokens, secrets, and personal data before publication.

## Reproduction

To inspect and install the publicly available agent:

```bash
git clone https://github.com/manaplatform/mana-agent.git
cd mana-agent
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
```

The project supports an interactive configuration flow:

```bash
mana-agent --configure
```

**Prediction-generation runner at the referenced revision** (illustrative command; verify actual run arguments and limits using saved `mana_cmd.txt`, shell history, `runner.toml`, and environment records):

```bash
python scripts/swe_bench/runner.py \
  --provider openai --model gpt-6-luna \
  --dataset princeton-nlp/SWE-bench_Verified \
  --output predictions-reproduction.jsonl
```

**Warning:** This reproduces the *historical runner configuration*, **not a compliant leaderboard experiment**: the referenced runner includes dataset `hints_text`. Before a fresh leaderboard attempt, remove that input from generation and validate benchmark-integrity controls. This runner also overwrites its `--output` file on startup. Always use a new output path, never the preserved original predictions. The example omits a timeout override because its actual setting was not yet established. The precise inference provider, backend, permitted tools, model settings, and package versions remain to be documented from original records.

Evaluation evidence can be rechecked through the official submission tooling after the final artifacts have been packaged and published:

```bash
# Run from a checkout of SWE-bench/experiments after the entry exists:
swebench submit verify evaluation/verified/<entry-directory> -s verified
```

This command verifies the published record against its logged evaluation outputs; it does **not** rerun agent inference or the Docker benchmark.

## Authors and Research Report

- **Authors:** **ACTION REQUIRED:** Add the actual contributor names; no verified author names have been supplied.
- **First author profile:** **ACTION REQUIRED:** Add a real public profile URL.
- **Academic/research affiliation:** **ACTION REQUIRED:** List real institutional affiliations only. No eligible affiliation has been verified.
- **Technical report or preprint:** **ACTION REQUIRED:** Publish a substantial public technical report or preprint and insert its working URL.

**Current SWE-bench Verified submission policy:** New entries require an open research publication or technical report and an author affiliated with an academic institution or established research lab. **These requirements are separate from, and do not waive, the benchmark-integrity rules violated by the historical hint-bearing run.** Publishing artifacts does not by itself establish eligibility. See the [SWE-bench Experiments README](https://github.com/SWE-bench/experiments).

## Links

- [Mana-Agent (source code)](https://github.com/manaplatform/mana-agent)
- [SWE-bench benchmark](https://github.com/SWE-bench/SWE-bench)
- [Official leaderboard submissions](https://github.com/SWE-bench/experiments)
- [Submission checklist](https://github.com/SWE-bench/experiments/blob/main/checklist.md)

---

<p align="center"><strong>Mana-Agent</strong><br /><em>From intention to execution. From execution to evidence.</em></p>
