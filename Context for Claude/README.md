# Context Repository

A centralized knowledge base for project context, standards, and session learnings. These markdown files serve as a persistent reference that I can search and update across conversations.

## Directory Structure

```
Context for Claude/
├── README.md (you are here)
├── Industry Standards/
│   └── API_571_Damage_Mechanisms.md
└── 5DOF Flight/
    └── Rocket_Flight_Simulation.md
```

## How This Works

**For me:** When I need context about a previous project or standard, I search these files for relevant information. If the files include frontmatter with metadata and related links, I can quickly understand what's covered and navigate to related topics.

**For you:** This eliminates repetitive context-setting. Instead of re-explaining a project in every conversation, I read the file and jump straight to work.

**Updates:** When I work on an established project, I update its markdown file rather than creating new dated versions. The file becomes a living document with running updates.

## File Structure

Each markdown file follows this format:

```markdown
---
title: Project/Topic Name
category: Broad category
status: Active | Archived | In Development
last_updated: YYYY-MM-DD
tags: [relevant, keywords]
related_files: 
  - Link to related file
---

# Project/Topic Name

## Overview
[Brief 2-3 sentence description of what this is]

## Key Components / Architecture
[Main parts and how they interact]

## Technical Details
[Algorithms, design decisions, important equations]

## Current Status / Known Issues
[What's working, what needs work]

## How to Use / Entry Points
[Where to start if working on this]
```

## Quick Links

- [5DOF Flight Simulation](5DOF%20Flight/Rocket_Flight_Simulation.md) — Hybrid rocket dynamics, Monte Carlo analysis, flight design optimization
- [API 571 Damage Mechanisms](Industry Standards/API_571_Damage_Mechanisms.md) — Engineering standards for pressure equipment
