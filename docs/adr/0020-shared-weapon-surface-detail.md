# 0020. One shared surface tile for weapon finishes

- **Status** proposed
- **Date** 2026-11-23
- **Decided by** agent (provisional)

## Context

The wood stocks, polymer grips and metal housings fill much of the first-person view. Fine procedural grain needs to filter smoothly as the player moves between a close view and a distant pickup.

## Decision

Extend ADR 0014 to allow a shared, generated 512 × 512 detail tile on shader-finished weapons and the frag. Its linear RGB channels hold brushed steel, polymer grain and walnut figure. The material samples it in object space with mipmaps. The AR-17 uses its existing 2048 × 2048 baked maps.

## Consequences

The tile adds one shared texture and three filtered samples per shaded fragment on these finishes. Rebuild the tile with `python tools/assets/gun_surface.py`. Both Godot and the Blender inspection sheets use the generated image.

[Weapon roster](../design/reviews/weapon-model-finish/roster.jpg) · [Baked gun textures](0014-baked-gun-textures.md)
