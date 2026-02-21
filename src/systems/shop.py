"""
Shop system for Life of a Burrb.

Handles shop state and purchasing logic, separate from shop rendering.
The shop has 5 tabs: chips, berries, gems, snowflakes, mushrooms.
"""


def try_buy_ability(
    shop_tab,
    shop_cursor,
    ABILITIES,
    chips_collected,
    ability_unlocked,
    tab_abs,
    tab_cur,
    tab_indices,
    biome_ability_unlocked,
    berries_collected,
    gems_collected,
    snowflakes_collected,
    mushrooms_collected,
):
    """Attempt to purchase the currently selected ability.

    Returns updated (chips_collected, berries_collected, gems_collected,
    snowflakes_collected, mushrooms_collected, ability_unlocked,
    biome_ability_unlocked) as a dict.
    """
    result = {
        "chips": chips_collected,
        "berries": berries_collected,
        "gems": gems_collected,
        "snowflakes": snowflakes_collected,
        "mushrooms": mushrooms_collected,
        "ability_unlocked": ability_unlocked,
        "biome_ability_unlocked": biome_ability_unlocked,
    }

    if shop_tab == 0:
        # Chip shop - original abilities
        cost = ABILITIES[shop_cursor][1]
        if not ability_unlocked[shop_cursor] and chips_collected >= cost:
            result["chips"] = chips_collected - cost
            new_unlocked = list(ability_unlocked)
            new_unlocked[shop_cursor] = True
            result["ability_unlocked"] = new_unlocked
    else:
        # Biome shop - use the right currency
        cost = tab_abs[shop_cursor][1]
        real_idx = tab_indices[shop_cursor]
        if not biome_ability_unlocked[real_idx] and tab_cur >= cost:
            new_bio = list(biome_ability_unlocked)
            new_bio[real_idx] = True
            result["biome_ability_unlocked"] = new_bio
            if shop_tab == 1:
                result["berries"] = berries_collected - cost
            elif shop_tab == 2:
                result["gems"] = gems_collected - cost
            elif shop_tab == 3:
                result["snowflakes"] = snowflakes_collected - cost
            elif shop_tab == 4:
                result["mushrooms"] = mushrooms_collected - cost

    return result
