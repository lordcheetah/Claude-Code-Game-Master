#!/usr/bin/env python3
"""
relay_discord.py — a Discord front-end for online multiplayer (Phase 3).

A SECOND transport onto the exact same inbox/outbox seam as the web relay
(lib/relay_server.py). The bot never touches the GM brain: it maps Discord users
to seats, forwards their messages into relay/inbox-discord.jsonl, and relays the
GM's narration (and plate images) from relay/outbox.jsonl into a channel. The GM
still `drain`s and `post`s exactly as before, and both transports can run at once
(each writes its own per-source inbox file).

Setup:
  1. Create a bot at https://discord.com/developers, enable the **Message
     Content Intent**, invite it to your server.
  2. Put DISCORD_BOT_TOKEN=... (and optionally DISCORD_CHANNEL_ID=...) in .env.
  3. `bash tools/gm-relay.sh discord`  (multiplayer must be ON with seats added).

In the channel:
  !seats            list seats and which are taken
  !join <name>      claim a seat (then just type to act)
  !leave            give up your seat
  !who              who is connected / owes an action
Anything a joined player types (not starting with !) becomes their action.

Needs the `discord` extra:  uv pip install "discord.py>=2.3.0"
"""

import os
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from relay_manager import RelayManager


def _need_discord():
    try:
        import discord  # noqa: F401
        return __import__("discord")
    except ImportError:
        sys.stderr.write(
            "The Discord transport needs discord.py.\n"
            "  Install:  uv pip install \"discord.py>=2.3.0\"\n")
        sys.exit(2)


def _chunks(text, n=1900):
    text = text or ""
    return [text[i:i + n] for i in range(0, len(text), n)] or [""]


def run(token, channel_id=None):
    discord = _need_discord()
    relay = RelayManager.for_active()

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    state = {
        "channel_id": int(channel_id) if channel_id else None,
        "seats": {},                       # discord_user_id -> seat slug
        "since": relay._last_id(relay.outbox),   # don't replay history on start
    }

    def seat_by_slug(slug):
        return next((s for s in relay.seats() if s["slug"] == slug), None)

    @client.event
    async def on_ready():
        print(f"Discord relay online as {client.user} "
              f"(campaign: {relay.campaign_dir.name}). "
              f"{'Bound to channel ' + str(state['channel_id']) if state['channel_id'] else 'Post a command to bind a channel.'}")
        client.loop.create_task(pump())

    async def pump():
        """Relay new GM narration from the outbox into the bound channel."""
        await client.wait_until_ready()
        while not client.is_closed():
            try:
                if state["channel_id"]:
                    ch = client.get_channel(state["channel_id"])
                    if ch:
                        for e in relay.feed(state["since"]):
                            state["since"] = max(state["since"], e["id"])
                            files = []
                            for fn in e.get("images", []):
                                p = relay.campaign_dir / "images" / fn
                                if p.is_file():
                                    files.append(discord.File(str(p)))
                            parts = _chunks(e.get("text", ""))
                            for i, part in enumerate(parts):
                                # attach images only to the last chunk
                                await ch.send(content=part or None,
                                              files=(files or None) if i == len(parts) - 1 else None)
            except Exception as ex:  # keep the loop alive
                sys.stderr.write(f"[discord pump] {ex}\n")
            await asyncio.sleep(2)

    @client.event
    async def on_message(msg):
        if msg.author == client.user:
            return
        content = (msg.content or "").strip()
        # Bind to the first channel a command is used in, if not preconfigured.
        if state["channel_id"] is None and content.startswith("!"):
            state["channel_id"] = msg.channel.id
        if state["channel_id"] and msg.channel.id != state["channel_id"]:
            return

        if content.startswith("!"):
            await handle_command(msg, content)
            return

        # A normal message from a seated player is an action.
        slug = state["seats"].get(msg.author.id)
        if not slug:
            return  # not joined — ignore ordinary chatter
        seat = seat_by_slug(slug)
        if not seat:
            return
        relay.touch_presence(slug, seat["player"])
        relay.submit(seat["player"], content, seat=slug, source="discord")
        try:
            await msg.add_reaction("📨")   # queued for the GM
        except discord.DiscordException:
            pass

    async def handle_command(msg, content):
        parts = content[1:].split(None, 1)
        cmd = (parts[0].lower() if parts else "")
        arg = (parts[1].strip() if len(parts) > 1 else "")
        claimed = {v: k for k, v in state["seats"].items()}

        if cmd == "seats":
            lines = []
            for s in relay.seats():
                tag = " — taken" if s["slug"] in claimed else ""
                dead = "" if s.get("status") == "alive" else " [fallen]"
                lines.append(f"• **{s['player']}** → {s.get('character') or '(no character yet)'}{tag}{dead}")
            await msg.channel.send("**Seats**\n" + "\n".join(lines)
                                   + "\n\nClaim one with `!join <name>`, then just type to act.")
        elif cmd == "join":
            seat = relay.match_seat(arg)
            if not seat or seat.get("status") != "alive":
                await msg.channel.send(f"No open seat matching `{arg}`. Try `!seats`.")
                return
            state["seats"][msg.author.id] = seat["slug"]
            relay.touch_presence(seat["slug"], seat["player"])
            await msg.channel.send(
                f"🎭 {msg.author.display_name} now plays **{seat['player']} → "
                f"{seat.get('character') or '(build your character)'}**. Type anything to act.")
        elif cmd == "leave":
            state["seats"].pop(msg.author.id, None)
            await msg.channel.send("You’ve left your seat.")
        elif cmd == "who":
            view = relay.presence_view()
            rows = []
            for v in view:
                if v.get("status") != "alive":
                    dot = "✗"
                elif v.get("control", "self") != "self":
                    dot = "◐"
                elif v["connected"]:
                    dot = "●"
                else:
                    dot = "○"
                mark = " ✓" if v.get("has_pending") else (" …" if v.get("waiting") else "")
                rows.append(f"{dot} {v['player']} → {v.get('character') or '?'}{mark}")
            await msg.channel.send("**At the table**\n" + "\n".join(rows))
        else:
            await msg.channel.send("Commands: `!seats`, `!join <name>`, `!leave`, `!who`. "
                                   "Otherwise just type to act.")

    client.run(token)


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Discord transport for GM multiplayer")
    ap.add_argument("--token", default=os.environ.get("DISCORD_BOT_TOKEN", ""))
    ap.add_argument("--channel", default=os.environ.get("DISCORD_CHANNEL_ID", ""))
    a = ap.parse_args()
    if not a.token:
        sys.stderr.write("No DISCORD_BOT_TOKEN set (in .env or --token).\n")
        sys.exit(2)
    run(a.token, channel_id=a.channel or None)


if __name__ == "__main__":
    main()
