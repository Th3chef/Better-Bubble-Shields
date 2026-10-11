# Changelog

## Next version (in testing)
- The Invisible style's hit flash now follows the Color option too (it kept the game's color).
- Every style is now built from the game's own shield material, re-extracted from the game at build time, with only the style's changes applied; the build stops with a plain message if the game changes what a style relies on.
- Clearer option texts: a Color option recolors the shield's glow and break effects even while the shield option is off; set it to Default to keep that shield vanilla.
- The Nexus upload skips drafts and pre-releases.
- The build now makes the mod zip itself, reproducibly.

## v7
- The Color option now also colors each shield's **hit flash**, the **glow on its generator** (the arcs and glowing core of the Relay and the Shield Generator Pack, the glowing band on the G/SH-39 grenade) and its **break effect**. Game Default keeps the game's look.
- The effects the shields share with the rest of the game are never changed: the mod uses its own recolored copies.
- Smaller download (the mod's own thumbnail is now 512x512).
- Patch-proofing: after a game update the build checks the game's shield files and rebuilds from them in one step.
- New V7 art.

## v6
- Renamed from Clear Bubble Shields to Better Bubble Shields.
- New **Invisible** style.
- New **Color** option for every shield with 11 colors, separate from the style.
- The FX-12 Relay and the G/SH-39 Shield have their own options.
- Honeycomb is the first (default) style and more visible; Clear - Medium is 50% and Clear - Low 25%.
- The Shield Generator Pack's style also covers the line along the top of its dome.
- New art and option icons.

## v5
- All files combined into one mod with options: a checkbox per shield and a Clear - Medium / Clear - Low / Honeycomb choice for each.

## v4
- Main file changed to a light, even tint (medium opacity); added the With Honeycomb optional file.

## v3
- All Shields main file (Relay, Shield Pack, Directional and G/SH-39), very faint.

## v1 - v2
- Shield Pack and Directional Shield (low, then medium opacity).
