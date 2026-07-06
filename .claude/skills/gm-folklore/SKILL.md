---
name: gm-folklore
description: Generate culturally-plausible folklore (beliefs, rituals, folk explanations) for any object or phenomenon in the world. Load when a scene needs a superstition, a local custom, a taboo, a folk cure, or the myth behind a landmark, relic, or natural event — to make a culture feel lived-in. Triggers include "generate folklore", "invent a belief/ritual/superstition", or "what do the locals say about this".
---

# Folklore Generator

Generate culturally-plausible folklore elements (beliefs, rituals, folk explanations) from any observable object or phenomenon.

## Workflow

*Each step's reference file must only be read AFTER the previous step's output has been completed and presented. Do NOT batch-read reference files. Reading a step's reference file counts as beginning that step.*

### Step 1: Load Taxonomy and Criteria

Read `references/taxonomy-criteria.md` to understand:
- The seven mechanisms by which folklore originates
- The three criteria an association must meet to become viable folklore

### Step 2: Generate Raw Associations

Given the input object/phenomenon, brainstorm 8-12 associations using the mechanisms from Step 1. Each association must meet all three viability criteria. Present these in a table with columns: Property/Aspect | Mechanism Used | Association.

### Step 3: Select Candidate

From the associations, select the one that sounds **least like an existing cultural or folklore association**. Prefer novelty over familiarity. State the selection and briefly justify why it has unexplored memetic potential.

### Step 4: Load Belief Creation Reference

Read `references/belief-creation.md` to understand how to transform an association into structured folklore outputs.

### Step 5: Generate Core Outputs

Using the selected association, generate:
1. **Belief** - The core assertion people hold about the object/phenomenon
2. **Ritual** - A practice that emerges from or reinforces the belief
3. **Folk Explanation** - The "just-so story" that explains why the belief is true

### Step 6: Load Expansion Reference

Read `references/expansion-paths.md` to understand how folklore evolves over time.

### Step 7: Write Final Output

Generate an **Expansion Path** showing how the belief might evolve through 5-8 stages (drift, inversion, iconography, meaning loss, etc.).

Write all four outputs (Belief, Ritual, Folk Explanation, Expansion Path) to the template at `assets/folklore-output.md`. Save the completed file to `.work/{project-name}/folklore-{object}.md` (project-name derived from PROJECT_ROOT). When the folklore is canon for the story, hand it to **bible-builder** to fold into `{PROJECT_ROOT}/bible/universe/` — do not write bible canon directly.
