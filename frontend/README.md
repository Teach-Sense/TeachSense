# TeachSense — Lecture Console

A single-screen lecturer dashboard for TeachSense's classroom intelligence system. Built as a **concept-proof restructure**: a visual-first rebuild after the previous full-product architecture proved too complex to iterate on quickly.

This phase covers **the lecturer dashboard only** — no sign-in, no student dashboard, no device registration. Just enough interface to prove the concept end-to-end before backend logic is built around it.

## What it does

The console walks through four states in a single session:

1. **Idle** — lecturer enters a lecture topic and the class being taught. Both fields must be filled before recording can start.
2. **Recording** — mic goes live (visual on-air indicator, waveform, running timer). This is when the microphone hardware would stream audio to the backend.
3. **Processing** — after "Stop," the AI generates comprehension questions and scores the session. (In the real flow, this includes relaying questions to the speaker device and listening for spoken responses.)
4. **Results** — a Teaching Effectiveness score (radial gauge, 0–100%) broken into two weighted components:
   - **Student Comprehension** — 70% weight
   - **Teaching Scope** — 30% weight

   Below the score, **Lecturing Tips** appear: topics to revisit (with notes on why), and the top 3 concrete actions for next time.

## Current status

This is a **frontend visual prototype**. There is no backend connection yet — the `MOCK_RESULT` object at the top of `LectureConsole.tsx` stands in for what the AI scoring pipeline will eventually return, and the Stop → Processing → Results transition is simulated with a timer rather than a real API call.

The goal of this phase is to let the backend engineer see and interact with the intended flow before writing the logic that drives it — recording ingestion, question generation, WebSocket delivery to the speaker device, and score computation.

## Tech stack

- **React 19** + **TypeScript**
- **Vite** (dev server / build)
- **Tailwind CSS v4**
- **lucide-react** (icons)

No routing library, no state management library, no backend calls — kept deliberately minimal for this phase.

## Getting started

```bash
npm install
npm run dev
```

Open the local URL Vite prints (typically `http://localhost:5173`).

## Project structure

```
src/
  pages/
    LectureConsole.tsx   ← the entire dashboard (self-contained)
  App.tsx                ← renders LectureConsole directly, no router
  index.css              ← Tailwind import only
```

## Design direction

The visual language is a **broadcast console** — mic input, on-air state, speaker output — rather than a generic SaaS dashboard, since the underlying hardware really is a microphone feeding a system that later speaks back through a speaker.

- **Color:** near-black graphite background, teal (`#3FD6C0`) for data/scoring, warm red-orange (`#FF5B39`) for the live/recording state
- **Type:** Space Grotesk for the page title, IBM Plex Mono for all numeric readouts (timer, percentages, weights), Inter for body copy and labels
- **Signature element:** the on-air record button — pulses and glows red while live, with an animated waveform and running timer beneath it

## What the backend needs to wire in next

Per the team's process — frontend first, then backend logic built around it — here's what this UI expects once real logic replaces the mock:

| UI moment | Needs from backend |
|---|---|
| Start Recording | Signal to hardware mic to begin capture; audio format/parameters (sample rate, bit depth, channel count) still to be confirmed — research required on what the microcontroller sends and in what format |
| Stop Recording | Recording ends; AI generates comprehension questions (count should be AI-determined, kept small); after ~1 minute, questions are sent to the speaker device over WebSocket |
| Speaker device flow | Speak question 1 → listen for response → speak question 2 → listen → speak question 3 → listen (sequential, not simultaneous) |
| Results | AI returns: overall score, comprehension sub-score, scope sub-score, topics to revisit (with notes), and exactly 3 top actions |

Two devices only for this phase: **microphone** (input) and **speaker** (output). No camera, no device registration flow — kept out of scope deliberately for cost and simplicity.

## Notes for whoever picks this up next

- `MOCK_RESULT` in `LectureConsole.tsx` is the single point to replace with a real API response — its shape (`overall`, `comprehension`, `scope`, `revisit[]`, `topActions[]`) is the contract the backend should match.
- The Stop → Processing → Results timing is currently a fixed ~2.6s `setTimeout` for demo purposes. Real processing (the ~1 minute wait + spoken Q&A) will need a proper loading/waiting state, not a fixed timer.
- No error states are built yet (e.g. mic permission denied, backend unreachable) — worth adding once real calls are wired in.