"""
src/rendering/shop.py
Shop rendering: draw_shop, get_shop_tab_info.
Moved from game.py Phase 4.

Note: get_shop_tab_info returns data; draw_shop renders it.
Both functions accept all their dependencies as parameters (no globals).
"""

import pygame

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# Font objects created once at module level (after pygame.init has been called)
def _get_fonts():
    font: pygame.font.Font = pygame.font.Font(None, 28)
    shop_font: pygame.font.Font = pygame.font.Font(None, 32)
    shop_title_font: pygame.font.Font = pygame.font.Font(None, 48)
    return font, shop_font, shop_title_font


def get_shop_tab_info(
    tab,
    ABILITIES,
    chips_collected,
    ability_unlocked,
    BIOME_ABILITIES,
    biome_ability_unlocked,
    berries_collected,
    gems_collected,
    snowflakes_collected,
    mushrooms_collected,
):
    """Get the abilities list, currency count, currency name, and colors for a shop tab.

    Returns a tuple:
        (tab_abilities, currency_count, currency_name, cur_color,
         bg_color, border_color, unlock_list, indices)
    """
    if tab == 0:
        return (
            ABILITIES,
            chips_collected,
            "chips",
            (255, 200, 50),
            (40, 30, 60),
            (100, 80, 160),
            ability_unlocked,
            list(range(len(ABILITIES))),
        )
    elif tab == 1:
        items = [(n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "berry"]
        indices = [
            i for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES) if cur == "berry"
        ]
        return (
            items,
            berries_collected,
            "berries",
            (255, 100, 120),
            (50, 25, 30),
            (180, 80, 100),
            biome_ability_unlocked,
            indices,
        )
    elif tab == 2:
        items = [(n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "gem"]
        indices = [
            i for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES) if cur == "gem"
        ]
        return (
            items,
            gems_collected,
            "gems",
            (100, 220, 255),
            (25, 40, 55),
            (80, 150, 200),
            biome_ability_unlocked,
            indices,
        )
    elif tab == 3:
        items = [
            (n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "snowflake"
        ]
        indices = [
            i
            for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES)
            if cur == "snowflake"
        ]
        return (
            items,
            snowflakes_collected,
            "snowflakes",
            (200, 220, 255),
            (30, 35, 55),
            (100, 130, 200),
            biome_ability_unlocked,
            indices,
        )
    else:
        items = [
            (n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "mushroom"
        ]
        indices = [
            i
            for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES)
            if cur == "mushroom"
        ]
        return (
            items,
            mushrooms_collected,
            "mushrooms",
            (100, 255, 150),
            (25, 45, 30),
            (80, 180, 100),
            biome_ability_unlocked,
            indices,
        )


def draw_shop(
    surface,
    shop_tab,
    shop_cursor,
    ABILITIES,
    chips_collected,
    ability_unlocked,
    BIOME_ABILITIES,
    biome_ability_unlocked,
    berries_collected,
    gems_collected,
    snowflakes_collected,
    mushrooms_collected,
):
    """
    Draw the ability shop screen with tabs!
    LEFT/RIGHT arrows switch between biome currency tabs.
    Each tab shows abilities you can buy with that currency.
    """
    font, shop_font, shop_title_font = _get_fonts()

    # Dark semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # Get info for current tab
    (
        tab_abilities,
        currency_count,
        currency_name,
        cur_color,
        bg_color,
        border_color,
        unlock_list,
        indices,
    ) = get_shop_tab_info(
        shop_tab,
        ABILITIES,
        chips_collected,
        ability_unlocked,
        BIOME_ABILITIES,
        biome_ability_unlocked,
        berries_collected,
        gems_collected,
        snowflakes_collected,
        mushrooms_collected,
    )
    num_items = len(tab_abilities)

    # Shop box
    box_w = 520
    box_h = 130 + num_items * 52 + 40
    box_x = (SCREEN_WIDTH - box_w) // 2
    box_y = (SCREEN_HEIGHT - box_h) // 2

    # Background with border
    pygame.draw.rect(surface, bg_color, (box_x, box_y, box_w, box_h), border_radius=12)
    pygame.draw.rect(
        surface, border_color, (box_x, box_y, box_w, box_h), 3, border_radius=12
    )

    # Tab bar at the top
    tab_names = ["Chips", "Berries", "Gems", "Snowflakes", "Mushrooms"]
    tab_colors = [
        (255, 200, 50),  # chips gold
        (255, 100, 120),  # berries red
        (100, 220, 255),  # gems cyan
        (200, 220, 255),  # snowflakes blue-white
        (100, 255, 150),  # mushrooms green
    ]
    tab_w = box_w // 5
    for ti, tname in enumerate(tab_names):
        tx = box_x + ti * tab_w
        ty = box_y + 4
        tw = tab_w - 2
        th = 28
        if ti == shop_tab:
            pygame.draw.rect(
                surface, border_color, (tx + 1, ty, tw, th), border_radius=5
            )
            ttxt = font.render(tname, True, tab_colors[ti])
        else:
            ttxt = font.render(tname, True, (100, 100, 100))
        surface.blit(ttxt, (tx + tw // 2 - ttxt.get_width() // 2, ty + 5))

    # Title for current tab
    tab_titles = [
        "CHIP SHOP",
        "BERRY SHOP",
        "GEM SHOP",
        "SNOWFLAKE SHOP",
        "MUSHROOM SHOP",
    ]
    title = shop_title_font.render(tab_titles[shop_tab], True, cur_color)
    surface.blit(title, (box_x + box_w // 2 - title.get_width() // 2, box_y + 38))

    # Currency count
    cur_str = f"Your {currency_name}: {currency_count}"
    cur_txt = shop_font.render(cur_str, True, cur_color)
    surface.blit(cur_txt, (box_x + box_w // 2 - cur_txt.get_width() // 2, box_y + 78))

    # Abilities list
    for row_i, (name, cost, key_hint, desc) in enumerate(tab_abilities):
        row_y = box_y + 118 + row_i * 52
        # Figure out which unlock index to check
        if shop_tab == 0:
            unlocked = unlock_list[row_i]
        else:
            unlocked = unlock_list[indices[row_i]]

        # Highlight selected row
        if row_i == shop_cursor:
            pygame.draw.rect(
                surface,
                (bg_color[0] + 30, bg_color[1] + 30, bg_color[2] + 30),
                (box_x + 10, row_y - 4, box_w - 20, 48),
                border_radius=6,
            )
            pygame.draw.rect(
                surface,
                border_color,
                (box_x + 10, row_y - 4, box_w - 20, 48),
                2,
                border_radius=6,
            )

        # Already unlocked?
        if unlocked:
            name_color = (100, 220, 100)  # green = owned
            status = "OWNED"
            status_color = (100, 220, 100)
        elif currency_count >= cost:
            name_color = (255, 255, 255)  # white = can buy
            status = f"{cost} {currency_name}"
            status_color = cur_color
        else:
            name_color = (120, 120, 120)  # gray = too expensive
            status = f"{cost} {currency_name}"
            status_color = (150, 80, 80)

        # Name
        name_txt = shop_font.render(name, True, name_color)
        surface.blit(name_txt, (box_x + 24, row_y))

        # Key hint
        if unlocked:
            key_txt = font.render(f"[{key_hint}]", True, (150, 200, 150))
        else:
            key_txt = font.render(f"[{key_hint}]", True, (100, 100, 100))
        surface.blit(key_txt, (box_x + 24, row_y + 24))

        # Description
        desc_txt = font.render(desc, True, (180, 180, 200))
        surface.blit(desc_txt, (box_x + 140, row_y + 24))

        # Cost / status on the right
        cost_txt = shop_font.render(status, True, status_color)
        surface.blit(cost_txt, (box_x + box_w - cost_txt.get_width() - 20, row_y + 4))

    # Instructions at the bottom
    instr = font.render(
        "LEFT/RIGHT tab | UP/DOWN select | ENTER buy | TAB close", True, (180, 180, 200)
    )
    surface.blit(
        instr, (box_x + box_w // 2 - instr.get_width() // 2, box_y + box_h - 30)
    )
