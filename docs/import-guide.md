# Import System Guide

Complete documentation for importing PDFs, documents, and modules into playable campaigns using RAG (Retrieval-Augmented Generation).

## Quick Start

```bash
# One command does everything
/import "path/to/book.pdf" "campaign-name"
```

This will:
1. Create the campaign folder structure
2. Extract text from the document
3. Generate vector embeddings for semantic search
4. Launch extraction agents to find NPCs, locations, items, and plots
5. Merge and save everything to world state

---

## Manual Step-by-Step Process

For more control or troubleshooting, run each step individually:

### Step 1: Vectorize the Document

```bash
bash tools/gm-extract.sh prepare "path/to/book.pdf" "campaign-name"
```

This will:
- Create the campaign folder structure
- Extract text from PDF/DOCX/TXT
- Split into ~3000 character chunks
- Generate embeddings using sentence-transformers
- Store vectors in ChromaDB at `world-state/campaigns/<name>/vectors/`

### Step 2: Extract Entities

The `/import` command automatically launches 4 parallel extraction agents:

| Agent | Queries For | Output |
|-------|-------------|--------|
| NPCs | characters, names, dialogue | `extracted/npcs.json` |
| Locations | places, rooms, settings | `extracted/locations.json` |
| Items | treasures, equipment, artifacts | `extracted/items.json` |
| Plots | quests, hooks, storylines | `extracted/plots.json` |

Each agent uses semantic search to find relevant content:
```bash
bash tools/gm-search.sh "character names dialogue" --rag-only -n 50
```

### Step 3: Merge Results

```bash
bash tools/gm-extract.sh merge "campaign-name"
```

Combines all agent outputs into unified JSON files and deduplicates entities.

### Step 4: Review Extraction

```bash
bash tools/gm-extract.sh review "campaign-name"
```

Shows counts and samples from each entity type. Review before saving.

### Step 5: Save to World State

```bash
bash tools/gm-extract.sh save rename "campaign-name"
```

Moves extracted data to final world state files. Strategies:
- `rename` - Rename duplicates with suffix (default)
- `skip` - Skip entities that already exist
- `overwrite` - Replace existing entities

### Step 6: Archive Extraction Files (Optional)

```bash
bash tools/gm-extract.sh archive "campaign-name"
```

Archives the `extracted/` folder after successful merge to keep campaign folder clean.

---

## RAG Query Tool

After importing, you can query the vectorized source material directly:

```bash
# Search both world state AND source material (default)
bash tools/gm-search.sh "dragon"

# Search source material only
bash tools/gm-search.sh "dragon" --rag-only -n 20

# Search world state only
bash tools/gm-search.sh "dragon" --world-only
```

---

## Using Source Material During Play

When RAG context is shown during gameplay, **USE IT**:
- Ground scene descriptions in source material prose
- Reference specific details (smells, sounds, features) from the original
- Ensure NPC dialogue matches their canonical voice
- Capture the author's writing style and atmosphere

Use **ALL returned passages** - even loosely related passages help maintain authentic tone.

---

## System Components

| Component | Path | Purpose |
|-----------|------|---------|
| RAG Extractor | `lib/rag/rag_extractor.py` | PDF→chunks→vectors |
| Vector Store | `lib/rag/vector_store.py` | ChromaDB interface |
| Embedder | `lib/rag/embedder.py` | sentence-transformers |
| Agent Extractor | `lib/agent_extractor.py` | Orchestrates workflow |
| Search CLI | `tools/gm-search.sh` | Unified search |
| Extract CLI | `tools/gm-extract.sh` | prepare/merge/save |
| Extractor Agents | `.claude/agents/extractor-*.md` | 4 specialized agents |
| Import Skill | `.claude/commands/import.md` | Import workflow |

---

## Troubleshooting

### No results from queries?
- Check vectors exist: `bash tools/gm-search.sh "test" --rag-only`
- Re-run prepare step if needed: `bash tools/gm-extract.sh prepare "file" "name"`

### Missing entities?
- Try different search terms
- Increase result count: `-n 50` instead of default
- Run extraction agent again with specific focus

### Duplicate entities?
- Run merge step to deduplicate
- Manual cleanup in JSON files if needed

### Extraction agents failing?
- Check `bash tools/gm-extract.sh validate "campaign-name"`
- Re-run failed agent types individually

---

## Supported File Formats

- **PDF** - Full support with text extraction
- **DOCX** - Microsoft Word documents
- **TXT** - Plain text files
- **MD** - Markdown files

---

## Performance Tips

- Large documents (500+ pages) may take several minutes to vectorize
- Extraction agents run in parallel for speed
- Vector store is persistent - no need to re-vectorize on restart
- Use `--rag-only` flag for faster searches when world state isn't needed
