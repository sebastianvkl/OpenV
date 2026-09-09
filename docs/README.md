# OpenV documentation

Start with the [project README](../README.md) for the product, real example and current scope.

| You want to… | Read |
|---|---|
| Run or develop OpenV | [Getting started](GETTING_STARTED.md) |
| Understand the evidence rules | [Verification philosophy](VERIFICATION_PHILOSOPHY.md) |
| Find source-code responsibilities | [Repository map](REPOSITORY_MAP.md) |
| Extend a domain or verifier | [Domain packs](DOMAIN_PACKS.md) |
| Understand the broader architecture | [Architecture](ARCHITECTURE.md) and [decision log](DECISIONS.md) |
| See completed work and remaining tasks | [Execution plan](EXECUTION_PLAN.md) |
| Record the current one-minute demo | [Demo plan and voiceover](DEMO_PLAN.md) |
| Deploy the website and engineering backend | [Deployment guide](../deploy/README.md) |
| Contribute a fix or integration | [Contributing](../CONTRIBUTING.md) |
| Check screenshot provenance | [Images](images/README.md) |

## Reading the design documents

[Project context](PROJECT_CONTEXT.md) describes the long-term product. Architecture and early decisions include conceptual interfaces and deferred integrations. Later dated decisions and the execution plan identify what is implemented and supersede older choices, including the change to one persistent Dalus model. The repository map lists actual modules, not proposed directory placeholders.

The first complete reference domain is an RC motor-glider. A minimal bracket regression validates the generic pipeline boundary; additional production domains, automatic Onshape/RMFG integrations and physical-flight release remain future work.

Historical planning/status notes are preserved in `DEMO_STATUS.md`, `SUBMISSION.md`, `CODEX_START_PROMPT.md` and the root `HANDOFF.md`. Use the current execution plan and demo plan for today's acceptance and recording instructions.
