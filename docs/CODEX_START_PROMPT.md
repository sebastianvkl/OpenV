# Prompt to paste into the first Codex chat

Read `AGENTS.md` and every document it references under `docs/`.

These files contain the complete project context from prior product and architecture work. Treat them as the source of truth unless I explicitly change a decision.

**Do not write implementation code yet.**

First do the following:

1. Summarize your understanding of the product in your own words.
2. Identify any contradictions, missing decisions, or assumptions that would block implementation.
3. Propose the simplest architecture that can produce the hackathon demo today.
4. Identify the highest-risk technical integrations and recommend which ones should be deferred until after the core loop works.
5. Review `docs/EXECUTION_PLAN.md` and update it if you believe the implementation order should change.
6. Propose the minimal schemas/interfaces for:
   - HardwareProject
   - Requirement + verification contract
   - Evidence
   - Experiment / design version
   - EngineeringBackend
7. Describe the first deterministic end-to-end test case: a deliberately bad aircraft design that the verification engine must fail for concrete reasons.

Optimize aggressively for getting this loop working end-to-end:

**user intent -> requirements -> design -> external verification -> failures -> Astra redesign -> re-verification -> evidence-backed PASS**

The project is verification-first. Do not spend time on CAD polish, assembly animation, PDF output, Onshape, RMFG, or extra integrations until the core verification loop is real and testable.

Remember the non-negotiable rule:

**Astra proposes. Tools execute. Evidence decides.**

Once you have completed the planning steps above, stop and wait for my approval before beginning implementation.

---

# Follow-up prompt after approving the plan

Implement the approved P0 plan now.

Keep an end-to-end runnable path at all times. Start with schemas, local state, deterministic verification, and the first intentionally failing aircraft fixture. Add Astra only after the verifier can independently fail and pass known cases.

After each meaningful milestone:

- run tests
- update `docs/EXECUTION_PLAN.md`
- record any changed architectural decision in `docs/DECISIONS.md`
- summarize what is now working and what still blocks the demo

Do not add P2 integrations until the core verification/redesign loop works.
