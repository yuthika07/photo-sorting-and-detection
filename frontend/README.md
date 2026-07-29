# Wedding Photo Organizer — Frontend

Next.js (App Router) + TypeScript + Tailwind CSS v4 + Framer Motion +
Lucide React + Zustand + Axios. No component library (no MUI,
Bootstrap, Ant Design, Chakra). See `DESIGN.md` for the visual system's
rationale.

## Setup

```bash
npm install
cp .env.local.example .env.local   # adjust NEXT_PUBLIC_API_BASE_URL if needed
npm run dev
```

Requires the backend (see `../backend/README.md`) running and reachable
at `NEXT_PUBLIC_API_BASE_URL` (defaults to `http://127.0.0.1:8000`).

## Verify

```bash
npm run build   # production build + full TypeScript check
npm run start   # serve the production build
```

## Folder structure

```
frontend/
├── app/
│   ├── layout.tsx        # root layout, self-hosted Inter font
│   ├── page.tsx           # composes AppChrome + PhotoGrid
│   └── globals.css          # Tailwind v4 import + design tokens (@theme) + textures
├── components/
│   ├── layout/
│   │   ├── TitleBar.tsx        # decorative traffic lights + app title
│   │   └── AppChrome.tsx         # the one continuous dark chrome surface
│   ├── people/
│   │   ├── PersonCard.tsx          # thumbnail, name, count, rename/export, gold selection
│   │   ├── PersonShelf.tsx           # horizontal recessed rail of PersonCards
│   │   └── RenamePersonModal.tsx       # rename dialog
│   ├── search/
│   │   ├── SearchBar.tsx                 # removable chips + add-person popover
│   │   └── PersonChip.tsx                  # one removable chip
│   ├── photos/
│   │   ├── PhotoGrid.tsx                     # filtered results + export action/result banner
│   │   └── PhotoCard.tsx                       # one result "print"
│   └── ui/
│       ├── Button.tsx                            # the one button primitive (brass/chrome/subtle)
│       └── Modal.tsx                               # the one modal primitive
├── lib/
│   ├── types.ts               # shared TS types, mirroring backend Pydantic schemas
│   ├── api/
│   │   ├── client.ts             # the one Axios instance + error normalization
│   │   ├── search.ts               # GET /search/photos
│   │   ├── export.ts                 # POST /export/photos
│   │   └── persons.ts                  # GET/PATCH /persons — see note below
│   └── store/
│       └── useAppStore.ts              # Zustand: people, selection, search, export state
└── DESIGN.md
```

## API layer

Every network call lives in `lib/api/` — components never import
`axios` directly. `search.ts` and `export.ts` are wired against the
backend's real, working endpoints (Phase 7 / Phase 8 of the backend
build). `persons.ts` is written against a `GET /persons` and
`PATCH /persons/{id}` contract that **does not exist on the backend
yet** — this was a frontend-only phase; adding those two endpoints is
a small, separate backend task. Until then, the People shelf renders a
normal "couldn't load people" state rather than crashing, and rename
calls will fail the same way.

## State management

Zustand (`lib/store/useAppStore.ts`) — chosen over plain Context
because several pieces of state change independently AND several async
actions need to touch more than one of them at once (selecting a
person re-triggers a search; renaming a person needs to patch both the
people list and any occurrence already sitting in search results).
Redux was intentionally not used, per the brief.

## Design

Modern skeuomorphic, desktop-software-styled (Lightroom / Capture One /
older Apple Photos / macOS pro-app references) — dark brushed-graphite
chrome, warm paper-toned content cards, a single reserved gold accent
for selection. Full rationale in `DESIGN.md`.
