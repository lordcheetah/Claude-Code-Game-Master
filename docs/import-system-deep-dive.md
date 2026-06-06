# Import System Deep Dive

Complete technical breakdown of the document import and extraction workflow.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         /import command                              │
│                    (.claude/commands/import.md)                      │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Step 1: PREPARE                                   │
│                  gm-extract.sh prepare                               │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              ContentExtractor (lib/content_extractor.py)     │   │
│  │  - PDFExtractor (pdfplumber → PyPDF2 fallback)              │   │
│  │  - MarkdownExtractor                                         │   │
│  │  - DocxExtractor                                             │   │
│  │  - TextExtractor                                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              SmartChunker (lib/smart_chunker.py)             │   │
│  │  - Splits text by headers or paragraph size (3000 chars)    │   │
│  │  - Scores each chunk with regex patterns                     │   │
│  │  - Categorizes: npc, location, item, plot, general          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AgentExtractor.prepare_for_agents()             │   │
│  │  - Creates campaign folder structure                         │   │
│  │  - Saves chunks to files with metadata headers              │   │
│  │  - Saves full text to current-document.txt                  │   │
│  │  - Saves metadata.json                                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Step 2: EXTRACT (Parallel Agents)                 │
│                                                                      │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌─────────────┐│
│  │extractor-npcs│ │extractor-    │ │extractor-    │ │extractor-   ││
│  │              │ │locations     │ │items         │ │plots        ││
│  │Read chunks/  │ │Read chunks/  │ │Read chunks/  │ │Read chunks/ ││
│  │npc_*.txt     │ │location_*.txt│ │item_*.txt    │ │plot_*.txt   ││
│  │              │ │              │ │              │ │             ││
│  │Write:        │ │Write:        │ │Write:        │ │Write:       ││
│  │npcs.json     │ │locations.json│ │items.json    │ │plots.json   ││
│  └──────────────┘ └──────────────┘ └──────────────┘ └─────────────┘│
│         │                │                │               │         │
│         └────────────────┴────────────────┴───────────────┘         │
│                                    │                                 │
│                                    ▼                                 │
│                          extracted/ folder                           │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Step 3: MERGE                                     │
│                  gm-extract.sh merge                                 │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AgentExtractor.merge_agent_results()            │   │
│  │  - Reads all extracted/*.json files                         │   │
│  │  - Combines into single merged-results.json                 │   │
│  │  - Handles list→dict conversion                             │   │
│  │  - Generates extraction_summary                             │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Step 4: REVIEW                                    │
│                  gm-extract.sh review                                │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AgentExtractor.review_extraction()              │   │
│  │  - Reads merged-results.json                                │   │
│  │  - Shows counts and sample names                            │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Step 5: SAVE (Optional)                           │
│                  gm-extract.sh save                                  │
│                         │                                            │
│                         ▼                                            │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │              AgentExtractor.validate_and_save()              │   │
│  │  - Checks for name conflicts with existing content          │   │
│  │  - Applies conflict strategy (rename/skip/overwrite)        │   │
│  │  - Calls NPCManager.create_batch()                          │   │
│  │  - Calls LocationManager.create_batch()                     │   │
│  │  - Saves items to extracted-items.json                      │   │
│  │  - Saves plots to extracted-plots.json                      │   │
│  │  - Logs event to session                                    │   │
│  └─────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Details

### 1. ContentExtractor (`lib/content_extractor.py`)

**Purpose**: Extract raw text from any document format.

**Supported formats**:
| Extension | Extractor | Libraries |
|-----------|-----------|-----------|
| `.pdf` | PDFExtractor | pdfplumber (primary), PyPDF2 (fallback) |
| `.md`, `.markdown` | MarkdownExtractor | Built-in |
| `.docx`, `.doc` | DocxExtractor | python-docx |
| `.txt`, `.text` | TextExtractor | Built-in |

**PDF extraction flow**:
1. Try pdfplumber (better for complex layouts)
2. If fails, fall back to PyPDF2
3. Add page markers (`--- Page N ---`)
4. Return combined text

---

### 2. SmartChunker (`lib/smart_chunker.py`)

**Purpose**: Split document into categorized chunks for parallel processing.

**Chunking algorithm**:
1. Try splitting by markdown headers (`# ## ###`)
2. If no headers, split by paragraphs
3. Target chunk size: ~3000 characters
4. Score each chunk for content type

**Scoring patterns** (regex matches per 100 chars):

| Category | Patterns (weight) |
|----------|-------------------|
| NPC (1.0) | `NPC`, `Character`, `AC`, `HP`, `CR`, dialogue verbs |
| Location (0.8) | `Room`, `Area`, directions, `door`, `feet` |
| Item (1.2) | `gp`, `sp`, weapon names, `magic`, rarity words, `+N weapon` |
| Plot (0.9) | `quest`, `mission`, conditionals, `rumor`, `reward` |

**Categorization rule**: Chunk goes to highest-scoring category if score > 1.2x other scores. Otherwise → `general_chunks`.

**Output structure**:
```
chunks/
├── npc_000.txt, npc_001.txt, ...
├── location_000.txt, location_001.txt, ...
├── item_000.txt, item_001.txt, ...
├── plot_000.txt, plot_001.txt, ...
└── general_000.txt, general_001.txt, ...
```

Each chunk file has a header:
```
# Chunk 1 of 5 (npc content)
# Confidence: 0.85
# Start line: ~42
---

[actual chunk text]
```

---

### 3. Extraction Agents (`.claude/agents/extractor-*.md`)

**Purpose**: AI agents that read chunks and extract structured data.

| Agent | Input | Output Key | Adapts To |
|-------|-------|------------|-----------|
| `extractor-npcs` | `chunks/npc_*.txt` + general | `npcs` | D&D NPCs, fiction characters, script characters |
| `extractor-locations` | `chunks/location_*.txt` + general | `locations` | Dungeons, settings, script scenes |
| `extractor-items` | `chunks/item_*.txt` + general | `items` | Magic items, props, notable objects |
| `extractor-plots` | `chunks/plot_*.txt` + general | `plot_hooks` | Quests, themes, scenes, ideas |

**Agent behavior**:
1. Read all assigned chunk files
2. Detect document type from content patterns
3. Extract entities matching their category
4. Merge duplicates (same character mentioned multiple times)
5. Write JSON to `extracted/npcs.json` (or locations, items, plots)

**Output schema** (example for NPCs):
```json
{
  "npcs": {
    "Character Name": {
      "name": "Character Name",
      "description": "80+ word description...",
      "attitude": "friendly|neutral|hostile|suspicious|helpful",
      "location_tags": ["Location 1"],
      "events": ["Quest involvement"],
      "stats": {"ac": 15, "hp": 45, "cr": "3"},
      "dialogue": ["Notable quote"],
      "source": "Document section"
    }
  }
}
```

---

### 4. AgentExtractor (`lib/agent_extractor.py`)

**Purpose**: Coordinate the entire extraction workflow.

**Key methods**:

| Method | What it does |
|--------|--------------|
| `prepare_for_agents(filepath)` | Extract text, chunk, save to campaign folder |
| `merge_agent_results()` | Combine all agent outputs into merged-results.json |
| `validate_and_save(data, strategy)` | Save to world state with conflict handling |
| `review_extraction()` | Show summary of extracted content |

**Conflict strategies**:
- `rename`: Add suffix like "Name (2)" to duplicates
- `skip`: Keep existing, ignore new
- `overwrite`: Replace existing with new

---

### 5. File Structure

**Campaign folder** (`world-state/campaigns/<name>/`):
```
world-state/campaigns/red-demon/
├── chunks/                    # Input for agents
│   ├── npc_000.txt
│   ├── npc_001.txt
│   ├── location_000.txt
│   └── ...
├── extracted/                 # Output from agents
│   ├── npcs.json             # From extractor-npcs agent
│   ├── locations.json        # From extractor-locations agent
│   ├── items.json            # From extractor-items agent
│   └── plots.json            # From extractor-plots agent
├── current-document.txt      # Full extracted text
├── metadata.json             # Extraction metadata
└── merged-results.json       # Combined from all agents
```

**World state** (after save):
```
world-state/
├── npcs.json                 # NPCs added here
├── locations.json            # Locations added here
├── extracted-items.json      # Items saved separately
├── extracted-plots.json      # Plots saved separately
└── campaigns/                # Original extractions preserved
```

---

## Data Flow Summary

```
Document.pdf
    │
    ▼
ContentExtractor.extract_text()
    │
    ▼
"Full plain text..."
    │
    ▼
SmartChunker.intelligent_split()
    │
    ▼
{
  npc_chunks: [{text, confidence, start_line}, ...],
  location_chunks: [...],
  item_chunks: [...],
  plot_chunks: [...],
  general_chunks: [...]
}
    │
    ▼
Save to chunks/*.txt files
    │
    ▼
4 Agents run in parallel, each reads relevant chunks
    │
    ▼
Write to extracted/*.json
    │
    ▼
merge_agent_results() combines all
    │
    ▼
merged-results.json
    │
    ▼
validate_and_save() → world-state/npcs.json, locations.json
```

---

## Key Design Decisions

1. **Parallel agents**: 4 agents run concurrently to maximize throughput
2. **Categorized chunks**: Pre-sorting by content type helps agents focus
3. **Isolated campaigns**: Each import goes to its own folder, never overwrites
4. **Deferred integration**: Review before saving to world state
5. **Content-type adaptation**: Agents detect D&D vs fiction vs scripts and adjust

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| No text extracted | PDF is image-only | Need OCR (not implemented) |
| All chunks are "general" | No strong content signals | Agents will still process |
| Merge fails | Agent didn't write output | Check extracted/*.json exists |
| Duplicates after save | Name conflicts | Use different conflict strategy |
| Missing NPCs/locations | Agent missed them | Re-run agent with specific prompt |
