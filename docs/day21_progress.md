# Day 21 — Loose Ends and Repository Cleanup

**Date:** Day 21
**Focus:** Bring the repository documentation up to date with the full scope of Days 1–20; fix naming inconsistency; prepare Phase 5 structure
**Deliverables:** Updated `README.md`, updated `docs/future_roadmap.md`, `docs/day21_progress.md`; manual rename instruction for `docs/day_12_progress.md`

---

## Summary

Days 1–20 built a complete RaceCAN software stack. The repository documentation did not reflect it. The README described only the Phase 1 simulator and an early file structure. The roadmap listed Phase 1 as "In progress." The day_12 progress log had an underscore in its filename that no other log has.

Day 21 fixes all three issues and closes out Phase 5 item 1–3 on the roadmap.

---

## What Was Done

### 1. README rewrite

The previous README described the project as a basic Python simulator with a terminal dashboard. It listed a file structure that did not reflect hardware documentation, firmware, BMS work, or any of Days 10–20.

The new README covers:

- System architecture block diagram (text-based, commit-ready)
- Full CAN frame map: primary frames 0x100–0x105 and BMS extension 0x200–0x205
- Hardware component table (MCU, CAN controller, transceiver, regulators, sensors)
- Protection summary
- Updated file structure covering all 20 days of deliverables
- How to run the simulator, BMS demo, and all three test suites
- BMS quick-start code example
- Fault state machine diagram
- Honest status section: what is and is not built in hardware
- Interview positioning: the core talking point for the project

The honest status section is deliberate. I decided early in this project that the strongest interview position is clarity about what has and has not been physically validated, backed by documented reasoning for why design-first is the right approach. An interviewer who asks "have you built this?" receives a clear answer and a documented explanation of the fault model and design decisions — not evasion.

### 2. future_roadmap.md update

The roadmap now reflects actual project state:

- Phase 1: Complete (all 10 goals marked DONE, including BMS and integration tests)
- Phase 2: Planned (dashboard polish — untouched)
- Phase 3: Complete (all 8 goals marked DONE)
- Phase 4: Planned — requires KiCad desktop tool; lists three open decisions that block capture
- Phase 5: In progress — includes knowledge assessment and circuitry assessment sessions
- Phase 6: Planned — requires component purchase

### 3. day_12_progress.md rename

The file `docs/day_12_progress.md` is the only progress log with an underscore between `day` and the number. All other logs follow `dayNN_progress.md`. This inconsistency is a broken convention that makes automation (log listing, link generation) fragile.

The fix is a GitHub web UI rename:

1. Open `docs/day_12_progress.md` in the GitHub file browser
2. Click the pencil (Edit) icon
3. In the filename field at the top of the editor, change `day_12_progress.md` to `day12_progress.md`
4. Scroll to the bottom and commit with message: `docs: rename day_12_progress.md to day12_progress.md (convention fix)`

GitHub's web editor treats a filename change as a delete-and-create in a single commit, so no history is lost.

---

## Locked Decisions

1. **Honest status section stays in the README**
   Documenting what has and has not been physically built is not a weakness. It is evidence of engineering discipline. The design-first approach is a deliberate choice, documented and defensible.

2. **Phase 5 includes active knowledge assessment, not passive documentation**
   Days 22 onward will include interactive Q&A sessions on protocol design, firmware architecture, fault logic, state machines, and circuit-level decisions. The goal is to ensure the project can be explained from first principles — not just pointed to on GitHub.

3. **future_roadmap.md is the authoritative phase tracker**
   The README references it. Progress logs reference it. It is the single source of truth for what is done and what is planned.

---

## Open Items Carried Forward

1. **day_12_progress.md rename** — must be done manually in GitHub web UI (instructions above)
2. **MP1584EN feedback divider** — open hardware decision, blocks Phase 4
3. **MCP2515 interrupt vs polling** — open firmware/hardware decision, blocks Phase 4
4. **D11–D13 SPI pin conflict** — documented in pin_mapping.md, blocks Phase 4
5. **Phase 2 dashboard polish** — planned but not scheduled

---
