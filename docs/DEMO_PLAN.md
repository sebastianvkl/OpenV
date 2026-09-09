# OpenV — one-minute submission demo

Recording plan, 2026-09-08. This replaces the earlier aspirational demo sequence with demonstrated functionality. The recording is now produced at `web/public/demo/openv-submission.mp4`: approximately 60 seconds, 1920×1080, H.264/AAC, with synthesized Samantha narration and burned-in captions. A caption sidecar and source manifest accompany it. Public link: https://openv-kohl.vercel.app/demo/openv-submission.mp4 . The event form has not been submitted by this recording workflow. No new engineering run was created.

## Submission brief

The participant guide supplied by the user requests a short **one-minute demo video**, a public repository, an accessible demo link, and all team members on the submission. It lists **5:30 p.m.** as the submission deadline; follow organizer updates if changed. The submission page could not be read from this session, so its current upload fields/limits are unconfirmed.

Submission: https://cerebralvalley.ai/e/openai-gpt-6-astra-sf/hackathon/submit
Public repository: https://github.com/sebastianvkl/OpenV
Public demo: https://openv-kohl.vercel.app

The guide explicitly requires identifying the functionality built during the event. Use this caption early: **“Built today: OpenV pipeline, Dalus MCP adapter, verification/redesign loop and browser demo.”** Dalus, AeroSandbox, the CAD kernel and other libraries are existing external tools. Say that Codex helped build the project; describe the actual development model/settings accurately if the form asks. Astra's runtime proposal and redesign calls are recorded in the engineering run.

## The story

A convincing CAD design contains a real installation error. External geometry checks expose it. Astra proposes a specific change from the measured failure, affected evidence is invalidated, and external verification evaluates the new version. The resulting aircraft remains a manufacturing candidate with explicit unknowns.

Use a recording of the actual completed run, labeled **“Recorded Astra run · computation time omitted.”** Cut between loaded states. Do not present historical version selection as a fresh live solver run, or the animation as a physical flight test. This is a working product demonstration with actual recorded engineering results, not slides.

## Prepare four tabs before recording

1. **Repair story:** https://openv-kohl.vercel.app/?run=run-dcef3705d89d . This is the actual Astra mission + redesign run. It has V01 and V02. In Simulate → Fit & access, V01 contains the failure; V02 contains the repaired result. Open its experiment log once to locate the battery change and “7 evidence records invalidated.”
2. **Dalus:** open the existing authenticated model `99ee8003-6171-47ce-903d-ad279e1b8f25`. Preselect the component-fit/insertion verification and show its requirements, latest result and retained test history. This same model now includes the later re-verification. If Dalus UI is unavailable, use OpenV's evidence drawer → “Dalus captured record,” clearly described as the captured MCP record. Do not create another model.
3. **Computed flight:** https://openv-kohl.vercel.app/?run=run-365c68904f40&view=flight . This is a subsequent verification of the same repaired candidate. Choose the power-loss response, 3× playback and a clear camera view. Rehearse Restart so zero thrust/descent is visible during the short clip.
4. **CAD payoff:** https://openv-kohl.vercel.app/?run=run-365c68904f40&view=assemble . Wait for STEP loaded, rehearse the exploded-view slider, then select a custom servo cradle and use Frame selected + Dimensions. Use a custom part so the close-up shows generated CAD detail. Purchased-part bodies remain labeled envelopes.

Record at 1920×1080 or 1600×900 if available, with the cursor visible and notifications silenced. Use a normal desktop layout and preloaded pages; omit download, login and STEP parsing waits. Capture the clips separately, then lay one voiceover across them. Aim for **58–60 seconds**. Keep the video link accessible without requiring a judge to request permission.

## Exact shot list

| Time | Show / action | Point to communicate |
|---|---|---|
| 0–5 s | Assembled aircraft in Explore, gentle orbit. | Convincing CAD is not proof. |
| 5–12 s | Recorded mission and evidence/requirements. Early caption identifies today's OpenV work. | Plain-English mission → requirements → Astra design; built with Codex. |
| 12–21 s | Repair tab → Simulate → Fit & access → V01. Use Detail or zoom into the battery region; show red interference and a collision row. | Independent geometry checks expose the actual battery/mount interference. |
| 21–32 s | Experiment log: battery change and “7 evidence records invalidated”; close log and choose V02. Show cleared collision checks. | Astra receives failure evidence, moves battery 3.6 mm, and independent re-verification evaluates the change. |
| 32–39 s | Switch to prepared Dalus model; show requirement/test/evidence history. | One persistent engineering model, accessed through MCP. |
| 39–46 s | Flight tab: computed power-loss animation with zero prescribed thrust and falling height. | AeroSandbox-based diagnostic, under stated assumptions. |
| 46–54 s | STEP tab: briefly explode, then close-up of custom CAD; point to candidate package download. | Real CAD, sourced BOM and manufacturing candidate outputs. |
| 54–60 s | Evidence totals: 16 PASS, 0 FAIL, 8 UNKNOWN. End with public repo/site URL overlay. | Explicit scope and honest unknowns; the LLM never grants PASS. |

Use short captions to make the numerical story readable: **“Battery x: 411.6 → 408.0 mm”**, **“7 evidence records invalidated”**, **“16 modeled PASS · 8 UNKNOWN.”** The 3.6 mm movement is visually small; the collision evidence and numbers establish the change. Do not exaggerate the geometry movement.

## Voiceover

AI can generate convincing CAD. But does the hardware actually work?

Today I built OpenV with Codex: an open-source pipeline connecting Astra to independent engineering verification.

For this motor-glider mission, Astra proposes requirements and a design. Geometry checks find the battery colliding with two servo mounts.

Astra receives that evidence and moves the battery forward 3.6 millimeters. Seven dependent evidence records are invalidated. Fresh checks clear the collisions.

Through MCP, Dalus holds requirements, parameters, tests and evidence in one persistent model.

AeroSandbox powers the analysis. This animation shows a computed power-loss response.

The output includes a full STEP assembly, sourced components and a manufacturing candidate package.

Sixteen modeled checks pass. Eight remain unknown, including physical flight. Astra proposes. Evidence decides.

Read at a comfortable pace; this is approximately 120 words. The shot boundaries are editing targets, not a reason to rush individual words. If long, remove “and a manufacturing candidate package” or shorten the CAD clip; preserve the failure, actual change, invalidation, external re-verification and unknowns.

## Exact evidence for the story

- Mission: “Build a conventional electric RC motor-glider carrying a 150 g camera for 20 minutes at 12 m/s. Use the current sourced installation catalog and verify the candidate.” The twenty-minute endurance is a target, not an achieved claim.
- Actual Astra run: `run-dcef3705d89d`, baseline `baseline-8cb2309a5029`.
- V01: `design-7e5e14a82ca4`, battery x = 0.4116 m. Static battery overlap is 10.45 mm³ with each of servo-mount-3 and servo-mount-4. Vertical insertion interference is 130.625 mm³ for each pair. These are solid-model results, not physical measurements.
- Astra experiment: `experiment-9e700b6c2adf`, battery x = 0.408 m; every other design parameter remains unchanged. Seven evidence records are invalidated.
- V02: `design-1e44b73937bc`; component-fit and component-insertion change FAIL → PASS. Final totals: 16 PASS / 0 FAIL / 8 UNKNOWN.
- Later unchanged-candidate verification: `run-365c68904f40`, design `design-34c4fb0ecbe1`, same persistent Dalus model, 45 CAD parts and 70 package hashes checked. This adds the computed flight-response diagnostics. The idealized power-loss case loses 16.62 m height by 25 s; do not promise that number will be visible during the abbreviated clip.
- Flight animation is a bounded point-mass prediction with idealized attitude tracking and prescribed thrust. Full structural, installation/retention and physical-flight release are not established.

## Submission copy

**Title:** OpenV — AI-generated hardware is a hypothesis

**Short description:** OpenV is an open-source hardware engineering pipeline: natural-language mission → Astra design → independent verification → evidence-driven redesign. In our motor-glider example, solid geometry checks find a battery collision; Astra moves it 3.6 mm, seven dependent evidence records are invalidated, and fresh checks clear the interference. Dalus is the persistent engineering record through MCP. The output includes CAD, sourced components, simulation diagnostics and a manufacturing candidate package. Sixteen modeled requirements pass; eight remain explicitly unknown, including physical flight.

**Built during the hackathon:** OpenV's runnable orchestration, proposal/verifier adapters, evidence invalidation and engineering experiments, Dalus MCP integration, aircraft CAD/verification implementation, public browser inspection/simulation experience and candidate-package outputs. Existing external tools are credited; Dalus itself was not newly built for this submission.

## Fallback

A previous 60-second recorded demo is already at https://openv-kohl.vercel.app/demo/openv-demo.mp4 (local `web/public/demo/openv-demo.mp4`). Its edit manifest identifies `run-38f998e18d41`, an earlier real Astra spar-redesign example. It does not show the newest installation repair, STEP inspection or flight-response work. Use it as the deadline fallback and describe its actual earlier run; do not pair the battery-repair narration above with that footage.
