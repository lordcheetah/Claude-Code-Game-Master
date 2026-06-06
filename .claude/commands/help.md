# /help - GM Command Reference

Display all available commands and tools.

---

## DISPLAY

```
================================================================
  GM ASSISTANT - Command Reference
================================================================

  CORE GAMEPLAY
  --------------------------------------------------------
  /gm              Play the game (handles everything)
  /gm save         Save current session state
  /gm character    Show character sheet & inventory
  /gm overview     View campaign state summary

  CAMPAIGN SETUP
  --------------------------------------------------------
  /new-game           Create a new campaign world
  /import             Import a PDF/document as campaign
  /create-character   Build a new player character
  /enhance            Enrich entities with source material

  UTILITY
  --------------------------------------------------------
  /reset           Clear campaign for fresh start
  /world-check     Validate campaign consistency
  /setup           Run installation (usually auto-detected)
  /help            This help message

================================================================

  CLI TOOLS (bash tools/gm-*.sh)
  --------------------------------------------------------
  gm-session.sh     Session management, save/restore
  gm-player.sh      Player character stats
  gm-npc.sh         Create and update NPCs
  gm-location.sh    Add and connect locations
  gm-consequence.sh Track future events
  gm-search.sh      Search world state
  gm-note.sh        Record world facts
  gm-enhance.sh     Enrich entities with RAG
  gm-overview.sh    Quick world summary
  gm-campaign.sh    Switch between campaigns

================================================================

  QUICK START
  --------------------------------------------------------
  New campaign:     /new-game
  Continue playing: /gm
  Import module:    /import

================================================================
```

---

## DETAILED HELP

If user asks for specific command help (e.g., `/help dm`), read and summarize that command file:

```bash
cat .claude/commands/[command].md | head -50
```

Provide a brief summary of what the command does and its key options.
