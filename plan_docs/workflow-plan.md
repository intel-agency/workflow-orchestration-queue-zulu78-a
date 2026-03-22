# Workflow Execution Plan: project-setup

**Generated:** 2026-03-22
**Dynamic Workflow:** `project-setup`
**Workflow File:** `ai_instruction_modules/ai-workflow-assignments/dynamic-workflows/project-setup.md`
**Repository:** intel-agency/workflow-orchestration-queue-zulu78-a

---

## 1. Overview

This document provides a comprehensive workflow execution plan for the `project-setup` dynamic workflow. The workflow orchestrates the initialization and foundation setup of the **OS-APOW (workflow-orchestration-queue)** project—a headless agentic orchestration platform that transforms GitHub Issues into automated execution orders.

**Workflow Summary:**
- **Total Main Assignments:** 5
- **Pre-script Events:** 1 (`create-workflow-plan`)
- **Post-assignment Events:** 2 per assignment (`validate-assignment-completion`, `report-progress`)
- **Primary Goal:** Initialize repository infrastructure, create application plan, establish project structure, and document learnings

**What the Workflow Accomplishes:**
1. Sets up GitHub Project for issue tracking with appropriate labels and columns
2. Creates a comprehensive application plan based on existing planning documents
3. Establishes the actual project scaffolding (Python/uv, Docker, CI/CD)
4. Generates AGENTS.md for AI coding agent context
5. Produces a debrief report capturing learnings and deviations

---

## 2. Project Context Summary

### Project Overview

**Project Name:** workflow-orchestration-queue (OS-APOW)
**Description:** A headless agentic orchestration platform that transforms GitHub Issues into automated execution orders. The system enables "Zero-Touch Construction" where users open specification issues and receive functional, test-passed branches and PRs without manual intervention.

**Core Components (The 4 Pillars):**
1. **The Ear (Work Event Notifier):** FastAPI webhook receiver for GitHub events
2. **The State (Work Queue):** GitHub Issues as distributed state ("Markdown as a Database")
3. **The Brain (Sentinel Orchestrator):** Background polling service that claims and dispatches tasks
4. **The Hands (Opencode Worker):** DevContainer-based AI execution environment

### Technology Stack

| Category | Technology | Version |
|----------|------------|---------|
| Language | Python | 3.12+ |
| Web Framework | FastAPI | Latest |
| ASGI Server | Uvicorn | Latest |
| Validation | Pydantic | Latest |
| HTTP Client | HTTPX | Latest (async) |
| Package Manager | uv | 0.10.9+ |
| Containerization | Docker / DevContainers | Latest |
| Shell Scripts | PowerShell Core / Bash | - |

### Repository Structure (Planned)

```
workflow-orchestration-queue/
├── pyproject.toml               # uv dependencies and metadata
├── uv.lock                      # Deterministic lockfile
├── src/
│   ├── notifier_service.py      # FastAPI webhook receiver
│   ├── orchestrator_sentinel.py # Background polling service
│   ├── models/
│   │   ├── work_item.py         # Unified WorkItem model + scrub_secrets()
│   │   └── github_events.py     # Webhook payload schemas
│   └── queue/
│       └── github_queue.py      # ITaskQueue + GitHubQueue implementation
├── scripts/
│   ├── devcontainer-opencode.sh # Shell bridge to worker
│   ├── gh-auth.ps1              # GitHub auth helper
│   └── update-remote-indices.ps1
├── local_ai_instruction_modules/
├── .devcontainer/
├── .github/
│   ├── workflows/
│   └── .labels.json
├── AGENTS.md
├── README.md
└── plan_docs/
```

### Key Constraints & Directives

1. **Action SHA Pinning:** All GitHub Actions MUST be pinned to specific commit SHAs (no `@v3` or `@main`)
2. **Assign-then-Verify Pattern:** Task claiming uses distributed locking via GitHub Assignees
3. **Credential Scrubbing:** All public logs must pass through `scrub_secrets()` utility
4. **Docker Healthchecks:** Use Python stdlib (no curl in containers)
5. **Connection Pooling:** Single `httpx.AsyncClient` instance per component
6. **Environment Variables:** Only 3 required for MVP: `GITHUB_TOKEN`, `GITHUB_ORG`, `SENTINEL_BOT_LOGIN`

### Existing Planning Documents

| Document | Purpose |
|----------|---------|
| `OS-APOW Development Plan v4.2.md` | Phased roadmap, user stories, risk assessment |
| `OS-APOW Architecture Guide v3.2.md` | System diagrams, ADRs, data flow |
| `OS-APOW Implementation Specification v1.2.md` | Detailed requirements, test cases, deliverables |
| `OS-APOW Plan Review.md` | Strengths, issues, recommendations from code review |
| `OS-APOW Simplification Report v1.md` | Applied simplifications and deferred features |
| `pr-approval-merge-plan.md` | PR workflow orchestration design |
| `src/models/work_item.py` | Reference implementation of unified model |
| `src/queue/github_queue.py` | Reference implementation of queue interface |

---

## 3. Assignment Execution Plan

### Pre-Script Event: create-workflow-plan

| Field | Content |
|-------|---------|
| **Assignment** | `create-workflow-plan`: Create Workflow Plan |
| **Goal** | Create a comprehensive workflow execution plan before other assignments begin |
| **Key Acceptance Criteria** | Dynamic workflow file read and understood; All assignments traced; All plan_docs/ read; Plan produced, approved, and committed |
| **Project-Specific Notes** | This is the current assignment. Plan docs are comprehensive and provide strong foundation. Existing code in plan_docs/src/ serves as reference implementation. |
| **Prerequisites** | None |
| **Dependencies** | None |
| **Risks/Challenges** | None - planning only |
| **Events** | None |

---

### Assignment 1: init-existing-repository

| Field | Content |
|-------|---------|
| **Assignment** | `init-existing-repository`: Initiate Existing Repository |
| **Goal** | Set up repository infrastructure including GitHub Project, labels, workspace configuration, and initial branch/PR |
| **Key Acceptance Criteria** | 1) Branch `dynamic-workflow-project-setup` created FIRST; 2) GitHub Project created with columns (Not Started, In Progress, In Review, Done); 3) Labels imported from `.github/.labels.json`; 4) Workspace/devcontainer files renamed; 5) PR created after first commit |
| **Project-Specific Notes** | Repository is template-derived; `.github/.labels.json` already exists; Scripts `import-labels.ps1` and `test-github-permissions.ps1` available; Must verify GitHub CLI auth scopes before proceeding |
| **Prerequisites** | GitHub auth with scopes: `repo`, `project`, `read:project`, `read:user`, `user:email` |
| **Dependencies** | None (first main assignment) |
| **Risks/Challenges** | GitHub Project API may require elevated scopes; PR creation requires at least one commit; Branch naming convention must match exactly |
| **Events** | Post: `validate-assignment-completion`, `report-progress` |

**Validation Commands:**
```powershell
# Verify permissions before starting
./scripts/test-github-permissions.ps1 -Owner intel-agency

# Import labels
./scripts/import-labels.ps1
```

---

### Assignment 2: create-app-plan

| Field | Content |
|-------|---------|
| **Assignment** | `create-app-plan`: Create Application Plan |
| **Goal** | Create a comprehensive application plan documented as a GitHub Issue with milestones and labels |
| **Key Acceptance Criteria** | 1) Application template analyzed; 2) `plan_docs/tech-stack.md` created; 3) `plan_docs/architecture.md` created; 4) Planning issue created using template; 5) Milestones created and linked; 6) `implementation:ready` label applied |
| **Project-Specific Notes** | Rich planning documents already exist in plan_docs/; Should synthesize OS-APOW Development Plan, Architecture Guide, and Implementation Spec into actionable planning issue; Reference implementations exist in plan_docs/src/ |
| **Prerequisites** | `init-existing-repository` complete; GitHub Project available for issue tracking |
| **Dependencies** | Outputs from Assignment 1 (Project, labels, milestones) |
| **Risks/Challenges** | Planning issue template may need adaptation for Python project; Must not implement code - planning only |
| **Events** | Pre: `gather-context`; Post: `validate-assignment-completion`, `report-progress`; On-failure: `recover-from-error` |

**Tech Stack Documentation (to be created):**
- Language: Python 3.12+
- Framework: FastAPI
- Package Manager: uv
- Testing: pytest
- Linting: ruff (Python), shellcheck (shell scripts)
- Containerization: Docker, DevContainers

---

### Assignment 3: create-project-structure

| Field | Content |
|-------|---------|
| **Assignment** | `create-project-structure`: Create Project Structure |
| **Goal** | Create actual project scaffolding including source directories, Docker configs, CI/CD workflows, and documentation |
| **Key Acceptance Criteria** | 1) Project structure created per tech stack; 2) Dockerfile and docker-compose.yml created; 3) CI/CD workflows established (SHA-pinned); 4) Documentation structure (README, docs/, ADRs); 5) `.ai-repository-summary.md` created; 6) Build succeeds |
| **Project-Specific Notes** | Python/uv project structure; Must move reference code from plan_docs/src/ to actual src/; Docker healthchecks must use Python stdlib (no curl); All GitHub Actions MUST be SHA-pinned to latest release |
| **Prerequisites** | `create-app-plan` complete; Tech stack documented |
| **Dependencies** | Planning issue from Assignment 2 provides implementation blueprint |
| **Risks/Challenges** | SHA lookup for GitHub Actions requires runtime API calls; Editable installs need source copied before `uv pip install -e .`; Docker compose healthcheck syntax |
| **Events** | Post: `validate-assignment-completion`, `report-progress` |

**Critical Implementation Notes:**
1. **Dockerfile:** When using `uv pip install -e .`, ensure `COPY src/ ./src/` appears BEFORE the install command
2. **docker-compose.yml healthcheck:** Use Python stdlib:
   ```yaml
   healthcheck:
     test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')"]
   ```
3. **GitHub Actions:** Pin all actions to full SHA with version comment:
   ```yaml
   uses: actions/checkout@b4ffde65f46336ab88eb53be808477a3936bae11 # v4.1.1
   ```

---

### Assignment 4: create-agents-md-file

| Field | Content |
|-------|---------|
| **Assignment** | `create-agents-md-file`: Create AGENTS.md File |
| **Goal** | Create AGENTS.md at repository root providing AI coding agents with context and instructions |
| **Key Acceptance Criteria** | 1) AGENTS.md exists at root; 2) Project overview and tech stack documented; 3) Setup/build/test commands verified; 4) Code style conventions documented; 5) Project structure documented; 6) All commands validated by running them |
| **Project-Specific Notes** | Must validate commands actually work in devcontainer; Cross-reference README.md and .ai-repository-summary.md; Follow agents.md specification (https://agents.md/) |
| **Prerequisites** | `create-project-structure` complete; Build and test commands available |
| **Dependencies** | Project structure must exist to document |
| **Risks/Challenges** | Commands must be verified by actual execution; AGENTS.md must complement not duplicate README |
| **Events** | Post: `validate-assignment-completion`, `report-progress` |

**Key Commands to Document and Validate:**
```bash
# Install dependencies
uv sync

# Run tests
uv run pytest

# Run linter
uv run ruff check .

# Build Docker image
docker build -t os-apow .

# Run devcontainer
./scripts/devcontainer-opencode.sh up
```

---

### Assignment 5: debrief-and-document

| Field | Content |
|-------|---------|
| **Assignment** | `debrief-and-document`: Debrief and Document Learnings |
| **Goal** | Perform comprehensive debriefing capturing learnings, deviations, and recommendations for future work |
| **Key Acceptance Criteria** | 1) Debrief report created with 12 sections; 2) Execution trace saved to `debrief-and-document/trace.md`; 3) All deviations documented; 4) Stakeholder approval obtained; 5) Report committed and pushed |
| **Project-Specific Notes** | Critical for self-bootstrapping system; Must capture any template repo issues; Flag plan-impacting findings as ACTION ITEMS; Review upcoming phases for continued validity |
| **Prerequisites** | All previous assignments complete |
| **Dependencies** | All assignment outputs for comprehensive review |
| **Risks/Challenges** | Must be thorough - future phases depend on captured learnings; 12-section template must be complete |
| **Events** | Post: `validate-assignment-completion`, `report-progress` |

**Required Report Sections:**
1. Executive Summary
2. Workflow Overview
3. Key Deliverables
4. Lessons Learned
5. What Worked Well
6. What Could Be Improved
7. Errors Encountered and Resolutions
8. Complex Steps and Challenges
9. Suggested Changes (by category)
10. Metrics and Statistics
11. Future Recommendations
12. Conclusion

---

### Post-Assignment Events

#### validate-assignment-completion

| Field | Content |
|-------|---------|
| **Goal** | Validate that completed assignment met all acceptance criteria |
| **When Executed** | After each main assignment completes |
| **Key Actions** | Check files exist; Run verification commands (build, test, lint); Create validation report; Determine pass/fail; Block progression if failed |
| **Executor** | Independent QA agent (`qa-test-engineer`) - not the implementer |

#### report-progress

| Field | Content |
|-------|---------|
| **Goal** | Report progress, capture outputs, and checkpoint state |
| **When Executed** | After each main assignment completes (and validation passes) |
| **Key Actions** | Generate structured progress report; Capture step outputs; Validate acceptance criteria; Create checkpoint state; Report deviations and plan-impacting discoveries |

---

## 4. Sequencing Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROJECT-SETUP WORKFLOW SEQUENCE                          │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────┐
│  PRE-SCRIPT EVENT           │
│  create-workflow-plan       │  ◄── CURRENT ASSIGNMENT
│  (this document)            │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐     ┌────────────────────────────┐
│  ASSIGNMENT 1               │     │  POST-EVENTS               │
│  init-existing-repository   │────►│  • validate-assignment-    │
│  • Create branch            │     │    completion              │
│  • Create GitHub Project    │     │  • report-progress         │
│  • Import labels            │     └────────────────────────────┘
│  • Rename workspace files   │
│  • Create PR                │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐     ┌────────────────────────────┐
│  ASSIGNMENT 2               │     │  PRE-EVENT                 │
│  create-app-plan            │────►│  gather-context            │
│  • Analyze plan_docs/       │     └────────────────────────────┘
│  • Create tech-stack.md     │
│  • Create architecture.md   │     ┌────────────────────────────┐
│  • Create planning issue    │────►│  POST-EVENTS               │
│  • Create milestones        │     │  • validate-assignment-    │
│  • Apply labels             │     │    completion              │
└─────────────┬───────────────┘     │  • report-progress         │
              │                     │  (on-failure: recover-     │
              ▼                     │   from-error)              │
┌─────────────────────────────┐     └────────────────────────────┘
│  ASSIGNMENT 3               │
│  create-project-structure   │     ┌────────────────────────────┐
│  • Create src/ structure    │────►│  POST-EVENTS               │
│  • Create Dockerfile        │     │  • validate-assignment-    │
│  • Create docker-compose    │     │    completion              │
│  • Create CI/CD workflows   │     │  • report-progress         │
│  • Create documentation     │     └────────────────────────────┘
│  • Create .ai-repo-summary  │
│  • Validate build           │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐     ┌────────────────────────────┐
│  ASSIGNMENT 4               │     │  POST-EVENTS               │
│  create-agents-md-file      │────►│  • validate-assignment-    │
│  • Gather project context   │     │    completion              │
│  • Validate commands        │     │  • report-progress         │
│  • Draft AGENTS.md          │     └────────────────────────────┘
│  • Cross-reference docs     │
│  • Final validation         │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐     ┌────────────────────────────┐
│  ASSIGNMENT 5               │     │  POST-EVENTS               │
│  debrief-and-document       │────►│  • validate-assignment-    │
│  • Create debrief report    │     │    completion              │
│  • Document deviations      │     │  • report-progress         │
│  • Flag ACTION ITEMS        │     └────────────────────────────┘
│  • Review with stakeholder  │
│  • Commit and push          │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│  WORKFLOW COMPLETE          │
│  Ready for Phase 1          │
│  implementation             │
└─────────────────────────────┘
```

---

## 5. Open Questions

The following questions should be addressed before or during workflow execution:

### Q1: Planning Document Source
**Question:** Should `create-app-plan` use the existing OS-APOW planning documents (Development Plan, Architecture Guide, Implementation Spec) as the primary source, or is a separate `ai-new-app-template.md` expected?

**Recommendation:** Use existing OS-APOW documents as primary source. They are comprehensive and already define the tech stack, architecture, and requirements. The assignment can create `tech-stack.md` and `architecture.md` by extracting and synthesizing from these documents.

**Status:** Pending stakeholder confirmation

---

### Q2: Already-Completed Initialization Steps
**Question:** The repository is already initialized from the template with `.github/.labels.json`, scripts/, and devcontainer configs. Should `init-existing-repository` detect and skip already-complete steps?

**Recommendation:** The assignment should verify each step and skip only if verification confirms completion. For example, if labels already exist, verify they match `.github/.labels.json` rather than blindly re-importing. However, branch and PR creation must still occur.

**Status:** Pending stakeholder confirmation

---

### Q3: Reference Code Location
**Question:** Should the reference implementations in `plan_docs/src/models/work_item.py` and `plan_docs/src/queue/github_queue.py` be moved to actual `src/` during `create-project-structure`, or are they purely reference material?

**Recommendation:** Move to actual `src/` directory during `create-project-structure`. These are working implementations that should be part of the project foundation, not just planning artifacts.

**Status:** Pending stakeholder confirmation

---

### Q4: GitHub Project Scope Requirements
**Question:** GitHub Project creation requires specific OAuth scopes (`project`, `read:project`). Are these scopes already configured for the workflow identity, or will manual intervention be needed?

**Recommendation:** Run `./scripts/test-github-permissions.ps1 -AutoFixAuth` before `init-existing-repository` to verify and attempt automatic scope resolution.

**Status:** Requires verification before Assignment 1

---

### Q5: CI/CD Workflow Scope
**Question:** The `create-project-structure` assignment mentions creating CI/CD workflows. Should these be the actual OS-APOW CI workflows (for the orchestrator project itself), or placeholder/template workflows?

**Recommendation:** Create actual CI workflows for the OS-APOW project: build, test, lint, and Docker build workflows. These will validate the project as it evolves. Reference existing `.github/workflows/` in the template for patterns.

**Status:** Pending stakeholder confirmation

---

## 6. Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GitHub Actions SHA lookup fails | High | Low | Use `gh api` to resolve latest release SHA; fallback to manual lookup |
| GitHub Project API scope missing | High | Medium | Pre-validate with `test-github-permissions.ps1`; request scope elevation if needed |
| Docker build fails due to healthcheck syntax | Medium | Low | Use Python stdlib pattern documented above; avoid curl dependency |
| Validation steps timeout | Medium | Medium | Configure reasonable timeouts; use incremental validation |
| Race condition in label/assignment operations | High | Low | Use assign-then-verify pattern; implement retries |
| AGENTS.md commands fail validation | Medium | Medium | Test each command in devcontainer before documenting |

---

## 7. Acceptance Criteria Summary

This workflow plan will be considered complete when:

- [x] Dynamic workflow file (`project-setup.md`) has been read and understood
- [x] Every workflow assignment has been traced and read
- [x] All documents in `plan_docs/` have been read and summarized
- [x] Workflow execution plan has been produced covering all assignments
- [x] Plan has been presented to stakeholder for approval
- [x] Approved plan is committed to `plan_docs/workflow-plan.md`

---

**Plan Prepared By:** Planner Agent
**Date:** 2026-03-22
**Status:** ✅ APPROVED
**Approved By:** Orchestrator
**Next Steps:** Proceed to Assignment 1 (init-existing-repository)
