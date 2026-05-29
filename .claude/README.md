# Shared Claude Code Setup (team)

This folder makes the team's Claude Code tooling travel with the repo. When you
clone or pull, you automatically get the same **skills** and **plugins** everyone
else uses — no manual install.

## How to activate (one time, per teammate)

1. `git pull` (or clone) — the skills land in `.claude/skills/`.
2. **Restart Claude Code** in this project. Skills and plugins load at startup.
3. First run will prompt you to trust the project plugins listed in
   `.claude/settings.json` — approve them. They come from the official
   `claude-plugins-official` marketplace, which Claude Code installs automatically.

That's it. Type `/` in Claude Code to see the skills, or just ask for design/UI
work and the relevant skill triggers on its own.

## What's shared

### Plugins (`.claude/settings.json` → official marketplace)
Coding/workflow: `code-review`, `code-simplifier`, `commit-commands`,
`feature-dev`, `pr-review-toolkit`, `security-guidance`, `claude-md-management`,
`terraform`, `superpowers`, `skill-creator`.
Design: `frontend-design`, `playground`.

### Skills (`.claude/skills/`)
| Skill | Use for |
|-------|---------|
| `web-design-guidelines` | Audit UI against Vercel's 100+ a11y/perf/UX rules |
| `vercel-react-best-practices` | Official Vercel React patterns |
| `emil-design-eng` | UI polish + animation philosophy (Emil Kowalski) |
| `impeccable` | Design vocabulary: polish / audit / critique / animate / bolder / quieter |
| `taste-skill` | Anti-slop landing pages, portfolios, redesigns |
| `animate` | Web animation implementation (Emil Kowalski's course) |
| `design-motion-principles` | Motion design audit + build, per-designer guidance |
| `minimalist-ui` | Minimalist aesthetic variant |
| `industrial-brutalist-ui` | Brutalist aesthetic variant |
| `high-end-visual-design` | Soft / high-end visual aesthetic variant |
| `redesign-existing-projects` | Audit-first redesign of existing UI |

## Personal vs. shared

- `.claude/settings.json` and `.claude/skills/` are **committed** (shared).
- `.claude/settings.local.json` stays **git-ignored** — put personal overrides
  (extra permissions, local MCP servers, personal plugins) there.

## Attribution & licenses (third-party — NOT student-authored)

These skills are vendored from upstream open-source repos for convenience. They are
external tooling that *assists* development; they are not part of the graded Hiver
codebase. Licenses belong to their authors:

| Skill(s) | Upstream | Author |
|----------|----------|--------|
| `web-design-guidelines`, `vercel-react-best-practices` | https://github.com/vercel-labs/agent-skills | Vercel |
| `emil-design-eng` | https://github.com/emilkowalski/skill | Emil Kowalski |
| `taste-skill` + variants | https://github.com/leonxlnx/taste-skill | Leon (leonxlnx) |
| `impeccable` | https://github.com/pbakaus/impeccable | Paul Bakaus (Apache-2.0) |
| `animate` | https://github.com/delphi-ai/animate-skill | Delphi |
| `design-motion-principles` | https://github.com/kylezantos/design-motion-principles | Kyle Zantos |
| `frontend-design`, `playground`, `superpowers` (plugins) | https://github.com/anthropics/claude-plugins-official | Anthropic |

To update a skill, re-pull from its upstream repo and copy the skill folder back
into `.claude/skills/`.
