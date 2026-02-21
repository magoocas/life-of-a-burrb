# Refactor Plan: Life of a Burrb

Restructuring the 6,044-line monolithic `game.py` into a well-organized multi-module project.

## Target Architecture

```
life-of-a-burrb/
├── game.py              # Entry point (tiny: imports + asyncio.run)
├── src/
│   ├── __init__.py
│   ├── constants.py     # Colors, dimensions, world size
│   ├── settings.py      # Screen, FPS, spawn config
│   ├── biomes.py        # Biome definitions, get_biome()
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── player.py    # Player class (position, HP, movement, tongue)
│   │   ├── building.py  # Building class (exterior + interior gen)
│   │   ├── npc.py       # NPC class + spawning
│   │   └── car.py       # Car class + spawning
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── abilities.py # All 21 abilities: definitions, state, timers, logic
│   │   ├── combat.py    # Tongue, NPC attacks, damage, knockback
│   │   ├── collision.py # can_move_to, can_move_interior, door detection
│   │   ├── camera.py    # Camera follow + earthquake shake
│   │   └── shop.py      # Shop state, tab info, purchasing logic
│   ├── world/
│   │   ├── __init__.py
│   │   └── generator.py # World generation (buildings, trees, parks, etc.)
│   ├── rendering/
│   │   ├── __init__.py
│   │   ├── world.py     # Ground, roads, trees, biome objects, collectibles
│   │   ├── entities.py  # Burrb, NPC, car drawing
│   │   ├── interior.py  # Interior drawing (rooms, furniture, resident, monster)
│   │   ├── effects.py   # Ability visual effects, tongue, flash, trails
│   │   ├── ui.py        # HUD (hearts, currencies, ability bars, prompts)
│   │   ├── shop.py      # Shop overlay rendering
│   │   └── jumpscare.py # Jumpscare rendering (simplified)
│   ├── input/
│   │   ├── __init__.py
│   │   ├── keyboard.py  # Keyboard event handling
│   │   └── touch.py     # Touch/mobile controls + button rendering
│   └── game.py          # GameState class + main loop
```

---

## Phase 1: Foundation (Low Risk)

- [x] Create `src/` package with `__init__.py`
- [x] Create `src/constants.py` — move all color constants and world dimensions
- [x] Create `src/settings.py` — move screen settings, FPS, spawn config
- [x] Create `src/biomes.py` — move biome constants, `BIOME_COLORS`, `get_biome()`
- [x] Update `game.py` imports, verify game runs
- [x] Commit + push

## Phase 2: Entity Classes

- [x] Create `src/entities/` package with `__init__.py`
- [x] Create `src/entities/building.py` — move the `Building` class
- [x] Create `src/entities/npc.py` — move the `NPC` class + NPC color/spawn data
- [x] Create `src/entities/car.py` — move the `Car` class + car color/spawn data
- [x] Create `src/entities/player.py` — new `Player` class encapsulating all player state (position, HP, facing, walk frame, tongue, currencies, interior state, hurt/death timers)
- [x] Verify game runs
- [x] Commit + push

## Phase 3: World Generation

- [x] Create `src/world/` package with `__init__.py`
- [x] Create `src/world/generator.py` — move all `random.seed(42)` world generation into `generate_world()` returning a `WorldData` dataclass
- [x] Verify game runs
- [x] Commit + push

## Phase 4: Rendering

- [ ] Create `src/rendering/` package with `__init__.py`
- [ ] Create `src/rendering/world.py` — move `draw_road_grid`, `draw_tree`, `draw_biome_object`, `draw_biome_collectible`, `draw_biome_ground`
- [ ] Create `src/rendering/entities.py` — move `draw_burrb`, `draw_npc_topdown`, `draw_car_topdown`
- [ ] Create `src/rendering/interior.py` — move `draw_interior_topdown`
- [ ] Create `src/rendering/effects.py` — extract ability visual effects + tongue rendering from main loop
- [ ] Create `src/rendering/ui.py` — extract HUD rendering (hearts, currencies, ability bars, prompts, title, death screen)
- [ ] Create `src/rendering/shop.py` — move `draw_shop` + `get_shop_tab_info`
- [ ] Create `src/rendering/jumpscare.py` — move + simplify `draw_jumpscare`
- [ ] Verify game runs
- [ ] Commit + push

## Phase 5: Game Systems

- [ ] Create `src/systems/` package with `__init__.py`
- [ ] Create `src/systems/abilities.py` — new `AbilityManager` class (21 abilities, unlock states, timers, cooldowns, per-frame updates)
- [ ] Create `src/systems/combat.py` — extract tongue mechanics, NPC attack/damage, resident/monster chase logic
- [ ] Create `src/systems/collision.py` — move `can_move_to`, `can_move_interior`, `get_nearby_door_building`, `is_at_interior_door`
- [ ] Create `src/systems/camera.py` — extract camera follow + earthquake shake
- [ ] Create `src/systems/shop.py` — shop state + purchasing logic (separate from rendering)
- [ ] Verify game runs
- [ ] Commit + push

## Phase 6: Input Handling

- [ ] Create `src/input/` package with `__init__.py`
- [ ] Create `src/input/keyboard.py` — extract keyboard event handling from main loop
- [ ] Create `src/input/touch.py` — move touch state, button defs, hit testing, drawing, event handling
- [ ] Verify game runs
- [ ] Commit + push

## Phase 7: GameState + Main Loop Restructure

- [ ] Create `src/game.py` with `GameState` class owning all state (Player, Camera, WorldData, AbilityManager, ShopState, etc.)
- [ ] Restructure the main loop into clean `handle_events(state)` → `update(state)` → `render(state)` phases
- [ ] Slim down root `game.py` to just entry point (~10 lines)
- [ ] Verify game runs
- [ ] Commit + push

## Phase 8: Code Simplification Pass

- [ ] Simplify jumpscare — data-driven level definitions instead of 500 lines of nested conditionals
- [ ] Simplify repetitive drawing — helper functions for common patterns (NPC types, car types, biome decorations)
- [ ] Remove any dead/redundant code found during restructuring
- [ ] Verify game runs
- [ ] Commit + push

## Phase 9: Deployment Update

- [ ] Update `.github/workflows/deploy.yml` to copy `src/` directory into `game_build/`
- [ ] Update `AGENTS.md` to reflect new multi-file architecture
- [ ] Commit + push

---

## Verification

After each commit, run:
```bash
source .venv/bin/activate && python3 game.py
```
Confirm the game launches and plays correctly. Fix any issues before moving on.

## Expected Outcome

- **Root `game.py`**: ~10 lines (entry point only)
- **`src/game.py`**: ~200-300 lines (GameState + main loop skeleton)
- **Largest module**: ~400-500 lines
- **Total line count**: ~4,500-5,000 (down from 6,044)
- **No behavioral changes** — the game plays identically
