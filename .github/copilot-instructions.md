# Project Overview: AI Simulated Patient (SP) Training Platform
An interactive clinical training app for medical students to practice history taking and physical examinations using natural dialogue and real-time voice models.

## Tech Stack
- Backend: Python 3.11+, FastAPI, WebSockets, Pydantic v2, SQLAlchemy (PostgreSQL / SQLite for dev).
- Frontend: Next.js 14+ (App Router), TypeScript, Tailwind CSS, Web Audio API (Linear PCM / Opus streaming).
- AI Engine: Real-time Audio/Text LLM with dynamic case prompt injection.

## Architecture Guidelines
1. Modular Architecture: Keep case validation, state management, audio streaming, and OSCE evaluation separated.
2. In-Character Constraints: The patient agent must never output AI meta-commentary, must use lay terms, and must gate clinical disclosures based on student questioning.
3. Type Safety: Strictly type all data models and WebSocket payload events with Pydantic and TypeScript interfaces.