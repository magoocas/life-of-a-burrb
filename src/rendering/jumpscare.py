"""
src/rendering/jumpscare.py
Jumpscare rendering: draw_jumpscare.
Moved from game.py Phase 4.
"""

import math
import random
import pygame

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT

# JUMPSCARE_DURATION must be in sync with game.py
JUMPSCARE_DURATION = 150


def draw_jumpscare(surface, frame, level=1):
    """
    Draw a jump scare that gets PROGRESSIVELY MORE TERRIFYING!
    Level 1: basic scare. Level 2+: each one worse than the last.
    More shake, bigger face, more blood, new nightmare effects,
    the birb gets closer, the screen breaks apart...
    """
    sw = SCREEN_WIDTH
    sh = SCREEN_HEIGHT
    lvl = max(1, level)  # scare intensity level

    # === SCALING FACTORS (everything gets worse!) ===
    shake_mult = 1.0 + lvl * 0.5  # shake gets more violent
    size_mult = 1.0 + lvl * 0.08  # face gets bigger each time
    blood_mult = 1.0 + lvl * 0.6  # more and more blood
    glitch_mult = 1.0 + lvl * 0.4  # more screen corruption
    flash_frames = 3 + lvl  # flash lasts longer each time

    # === PHASE 1: BLINDING FLASH ===
    if frame < flash_frames // 2:
        surface.fill((255, 255, 255))
        return
    if frame < flash_frames:
        # At higher levels, flash alternates white/red rapidly (strobe!)
        if lvl >= 3 and frame % 2 == 0:
            surface.fill((255, 255, 255))
        else:
            surface.fill((255, 0, 0))
        return

    # === SCREEN SHAKE (scales with level) ===
    base_shake = int(20 * shake_mult)
    if frame < 40:
        shake_intensity = min(base_shake, int(frame * 2 * shake_mult))
    elif frame < 100:
        shake_intensity = max(0, base_shake - (frame - 40) // 3)
    else:
        # At higher levels, shake NEVER fully stops
        shake_intensity = min(lvl * 2, 12)
    shake_x = random.randint(-shake_intensity, shake_intensity)
    shake_y = random.randint(-shake_intensity, shake_intensity)

    # === THE BIRB LUNGES AT YOU (faster and bigger at higher levels) ===
    lunge_speed = 3.0 + lvl  # lunges faster each time
    if frame < flash_frames + 3:
        grow = (frame - flash_frames) / lunge_speed
    else:
        grow = 1.0
    lunge = min(1.0, frame / max(1, 60 - lvl * 8))
    base_size = int((400 + lvl * 40) * size_mult)
    size = int((base_size + lunge * 150) * max(0.01, grow))
    if size < 10:
        return

    cx = sw // 2 + shake_x
    cy = sh // 2 + shake_y - 20

    # === BACKGROUND (gets darker and more red at higher levels) ===
    bg_r = min(30, lvl * 8)
    surface.fill((bg_r, 0, 0))

    # === FLICKERING STATIC (more intense at higher levels) ===
    static_count = int(80 * glitch_mult)
    if frame % max(1, 4 - lvl) == 0:
        for _ in range(static_count):
            rx = random.randint(0, sw)
            ry = random.randint(0, sh)
            rw = random.randint(2, int(40 * glitch_mult))
            rh = random.randint(1, max(2, int(3 * glitch_mult)))
            brightness = random.randint(40, min(140, 60 + lvl * 20))
            rc = (brightness, 0, 0)
            pygame.draw.rect(surface, rc, (rx, ry, rw, rh))

    # === BLOOD DRIPS (more drips, thicker, faster at higher levels) ===
    blood_seed = random.Random(42 + lvl)  # different pattern each level
    num_drips = int(20 * blood_mult)
    for i in range(num_drips):
        drip_x = blood_seed.randint(0, sw)
        drip_speed = blood_seed.uniform(2.0, 4.0 + lvl * 1.5)
        drip_len = blood_seed.randint(40, int(200 * blood_mult))
        drip_width = blood_seed.randint(2, max(3, 4 + lvl))
        drip_y = int(frame * drip_speed) - blood_seed.randint(0, 100)
        if drip_y > -drip_len:
            drip_top = max(0, drip_y - drip_len)
            drip_bot = min(sh, drip_y)
            if drip_bot > drip_top:
                pygame.draw.line(
                    surface,
                    (160, 0, 0),
                    (drip_x, drip_top),
                    (drip_x, drip_bot),
                    drip_width,
                )
                pygame.draw.circle(
                    surface, (180, 0, 0), (drip_x, drip_bot), drip_width + 1
                )

    # === LEVEL 4+: SCRATCHES ON THE SCREEN (claw marks!) ===
    if lvl >= 4:
        scratch_seed = random.Random(frame // 10 + lvl)
        num_scratches = lvl - 2
        for _ in range(num_scratches):
            s_x1 = scratch_seed.randint(0, sw)
            s_y1 = scratch_seed.randint(0, sh)
            s_x2 = s_x1 + scratch_seed.randint(-200, 200)
            s_y2 = s_y1 + scratch_seed.randint(50, 200)
            for offset in range(-2, 3):
                pygame.draw.line(
                    surface,
                    (100, 0, 0),
                    (s_x1 + offset * 4, s_y1),
                    (s_x2 + offset * 4, s_y2),
                    random.randint(1, 3),
                )

    # === THE SCARY BIRB BODY (bigger each time) ===
    body_w = int(size * 1.2)
    body_h = int(size * 1.3)
    body_color = (max(0, 25 - lvl * 3), max(0, 15 - lvl * 2), max(0, 30 - lvl * 3))
    pygame.draw.ellipse(
        surface,
        body_color,
        (cx - body_w // 2, cy - body_h // 3, body_w, body_h),
    )
    pygame.draw.ellipse(
        surface,
        (15, 5, 15),
        (cx - body_w // 2, cy - body_h // 3, body_w, body_h),
        max(3, size // 20),
    )

    # === SPIKY HAIR (more spikes at higher levels) ===
    spike_base_y = cy - body_h // 3
    num_spikes = 11 + lvl * 2
    for i in range(num_spikes):
        spike_x = cx - size // 2 + i * size // max(1, num_spikes - 1)
        spike_h = random.randint(size // 3, int(size * (0.5 + lvl * 0.08)))
        spike_w = random.randint(size // 14, size // 8)
        spike_color = (
            random.randint(10, 30),
            random.randint(5, 15),
            random.randint(15, 35),
        )
        pygame.draw.polygon(
            surface,
            spike_color,
            [
                (spike_x - spike_w, spike_base_y + 8),
                (spike_x + random.randint(-5, 5), spike_base_y - spike_h),
                (spike_x + spike_w, spike_base_y + 8),
            ],
        )

    # === EYES (pulse faster, glow brighter at higher levels) ===
    eye_y = cy + size // 15
    eye_spacing = int(size * 0.28)
    eye_size = size // 5

    pulse_speed = 0.15 + lvl * 0.05  # heartbeat gets faster!
    pulse = abs(math.sin(frame * pulse_speed)) * 0.4 + 0.6
    glow_size = int(eye_size * (1.3 + pulse * 0.3 + lvl * 0.1))

    # Level 3+: extra eyes appear!
    eye_positions = [cx - eye_spacing, cx + eye_spacing]
    if lvl >= 3:
        eye_positions.append(cx)
    if lvl >= 5:
        eye_positions.append(cx - eye_spacing * 2)
        eye_positions.append(cx + eye_spacing * 2)

    for idx, eye_x in enumerate(eye_positions):
        ey = eye_y if idx < 2 else eye_y - eye_size
        gs = min(glow_size, 120)
        glow_surf = pygame.Surface((gs * 4, gs * 4), pygame.SRCALPHA)
        for ring in range(gs, 0, -3):
            alpha = max(0, min(255, int((60 + lvl * 10) * (1.0 - ring / gs) * pulse)))
            pygame.draw.circle(
                glow_surf,
                (255, 0, 0, alpha),
                (gs * 2, gs * 2),
                ring,
            )
        surface.blit(glow_surf, (eye_x - gs * 2, ey - gs * 2))

        # Eye
        pygame.draw.circle(surface, (140, 0, 0), (eye_x, ey), eye_size + 6)
        pygame.draw.circle(
            surface,
            (int(255 * pulse), 0, 0),
            (eye_x, ey),
            eye_size,
        )
        # Veins (more at higher levels)
        num_veins = 8 + lvl * 2
        for v in range(num_veins):
            vein_angle = v * (2 * math.pi / num_veins) + random.uniform(-0.2, 0.2)
            vein_len = eye_size * random.uniform(0.5, 0.95)
            vx = eye_x + int(math.cos(vein_angle) * vein_len)
            vy = ey + int(math.sin(vein_angle) * vein_len)
            pygame.draw.line(
                surface,
                (100, 0, 0),
                (eye_x, ey),
                (vx, vy),
                1 + (1 if lvl >= 3 else 0),
            )
        # Pupil (gets SMALLER each level = creepier)
        pupil_size = max(2, eye_size // (5 + lvl))
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, ey), pupil_size)
        # Glint
        pygame.draw.circle(
            surface,
            (255, 200, 200),
            (eye_x - pupil_size, ey - pupil_size),
            max(1, pupil_size // 2),
        )

    # Eyebrows
    brow_thick = max(3, size // 25) + lvl
    pygame.draw.line(
        surface,
        (10, 0, 0),
        (cx - eye_spacing - eye_size - 5, eye_y - eye_size - 8),
        (cx - eye_spacing + eye_size + 5, eye_y - eye_size + 12),
        brow_thick,
    )
    pygame.draw.line(
        surface,
        (10, 0, 0),
        (cx + eye_spacing - eye_size - 5, eye_y - eye_size + 12),
        (cx + eye_spacing + eye_size + 5, eye_y - eye_size - 8),
        brow_thick,
    )

    # === THE MOUTH (opens wider, more teeth at higher levels) ===
    mouth_y = cy + int(size * 0.35)
    mouth_w = int(size * (0.85 + lvl * 0.03))
    mouth_h = int(size * (0.55 + lvl * 0.04))
    jaw_open = min(1.0, frame / max(1, 20 - lvl * 2))
    mouth_h = int(mouth_h * (0.6 + jaw_open * 0.4))

    pygame.draw.ellipse(
        surface,
        (15, 0, 0),
        (cx - mouth_w // 2, mouth_y - mouth_h // 4, mouth_w, mouth_h),
    )
    inner_w = int(mouth_w * 0.75)
    inner_h = int(mouth_h * 0.65)
    pygame.draw.ellipse(
        surface,
        (120, 5, 5),
        (cx - inner_w // 2, mouth_y + mouth_h // 10, inner_w, inner_h),
    )
    throat_r = max(8, size // 10) + lvl * 3
    pygame.draw.circle(surface, (5, 0, 0), (cx, mouth_y + mouth_h // 3), throat_r)

    # === TEETH (more teeth, longer, more blood each level) ===
    num_teeth = 13 + lvl * 2
    tooth_w = max(4, mouth_w // (num_teeth + 1))

    for i in range(num_teeth):
        tx = (
            cx
            - mouth_w // 2
            + tooth_w // 2
            + i * (mouth_w - tooth_w) // max(1, num_teeth - 1)
        )
        tooth_h = random.randint(size // 6, int(size * (0.33 + lvl * 0.04)))
        tooth_color = (220, 210, 180) if i % 3 == 0 else (245, 240, 230)
        if lvl >= 5 and i % 4 == 0:
            tooth_color = (220, 180, 180)
        jag = random.randint(-3, 3)
        pygame.draw.polygon(
            surface,
            tooth_color,
            [
                (tx - tooth_w // 2 - 1, mouth_y - mouth_h // 8),
                (tx + jag, mouth_y - mouth_h // 8 + tooth_h),
                (tx + tooth_w // 2 + 1, mouth_y - mouth_h // 8),
            ],
        )
        pygame.draw.line(
            surface,
            (180, 170, 150),
            (tx, mouth_y - mouth_h // 8 + 2),
            (tx + jag, mouth_y - mouth_h // 8 + tooth_h - 2),
            1,
        )
        blood_len = random.randint(
            int(size * 0.12 * blood_mult), int(size * 0.4 * blood_mult)
        )
        blood_width = random.randint(1, max(2, 2 + lvl))
        pygame.draw.line(
            surface,
            (random.randint(140, 200), 0, 0),
            (tx + jag, mouth_y - mouth_h // 8 + tooth_h),
            (
                tx + jag + random.randint(-4, 4),
                mouth_y - mouth_h // 8 + tooth_h + blood_len,
            ),
            blood_width,
        )

    # Bottom row
    for i in range(num_teeth):
        tx = (
            cx
            - mouth_w // 2
            + tooth_w // 2
            + i * (mouth_w - tooth_w) // max(1, num_teeth - 1)
        )
        tooth_h = random.randint(size // 6, int(size * (0.33 + lvl * 0.04)))
        tooth_color = (235, 230, 215) if i % 2 == 0 else (215, 200, 170)
        bottom_y = mouth_y + mouth_h - mouth_h // 4
        jag = random.randint(-3, 3)
        pygame.draw.polygon(
            surface,
            tooth_color,
            [
                (tx - tooth_w // 2 - 1, bottom_y),
                (tx + jag, bottom_y - tooth_h),
                (tx + tooth_w // 2 + 1, bottom_y),
            ],
        )
        if random.random() > 0.2:
            blood_len = random.randint(size // 10, int(size * 0.2 * blood_mult))
            pygame.draw.line(
                surface,
                (200, 10, 10),
                (tx + jag, bottom_y - tooth_h),
                (tx + jag + random.randint(-3, 3), bottom_y - tooth_h - blood_len),
                max(1, 1 + lvl // 2),
            )

    # Beak edges
    beak_color = (180, 100, 10)
    beak_thick = max(3, size // 30) + lvl
    pygame.draw.arc(
        surface,
        beak_color,
        (cx - mouth_w // 2 - 8, mouth_y - mouth_h // 2, mouth_w + 16, mouth_h // 2),
        0,
        math.pi,
        beak_thick,
    )
    pygame.draw.arc(
        surface,
        beak_color,
        (cx - mouth_w // 2 - 8, mouth_y + mouth_h // 2, mouth_w + 16, mouth_h // 2),
        math.pi,
        math.pi * 2,
        beak_thick,
    )

    # === BLOOD SPLATTER (way more at higher levels) ===
    splat_count = int(20 * blood_mult)
    for _ in range(splat_count):
        bx = cx + random.randint(-mouth_w, mouth_w)
        by = mouth_y + random.randint(-mouth_h, mouth_h)
        br = random.randint(3, max(6, int(size * 0.04 * blood_mult)))
        pygame.draw.circle(surface, (random.randint(130, 220), 0, 0), (bx, by), br)
    streak_count = int(6 * blood_mult)
    for _ in range(streak_count):
        sx = cx + random.randint(-size // 2, size // 2)
        sy = cy + random.randint(-size // 4, size // 2)
        ex = sx + random.randint(-80, 80)
        ey = sy + random.randint(20, 100)
        pygame.draw.line(
            surface,
            (160, 0, 0),
            (sx, sy),
            (ex, ey),
            random.randint(2, 3 + lvl),
        )

    # === LEVEL 2+: TEXT GETS MORE UNHINGED ===
    if frame > flash_frames:
        font_size = max(36, int(size * (0.33 + lvl * 0.05)))
        scare_font = pygame.font.Font(None, font_size)
        if lvl == 1:
            messages = ["AAAAAHHH!!!", "SCREEEEECH!", "GET OUT!!!", "RAAAAWWW!!!"]
        elif lvl == 2:
            messages = ["COME BACK...", "I SEE YOU", "SCREEEEECH!", "YOU CAN'T HIDE"]
        elif lvl == 3:
            messages = [
                "I FOUND YOU AGAIN",
                "WHY DO YOU KEEP COMING BACK",
                "SCREEEEE!",
                "THERE IS NO ESCAPE",
            ]
        elif lvl == 4:
            messages = [
                "DID YOU MISS ME?",
                "I'M ALWAYS IN THE CLOSET",
                "ALWAYS WATCHING",
                "I KNOW WHERE YOU LIVE",
            ]
        else:
            messages = [
                "I'M IN EVERY CLOSET NOW",
                "YOU SHOULD HAVE STOPPED",
                "THIS IS YOUR FAULT",
                "I WILL NEVER LEAVE",
            ]
        msg_idx = (frame // max(5, 20 - lvl * 3)) % len(messages)
        msg = messages[msg_idx]
        scare_text = scare_font.render(
            msg,
            True,
            (255, random.randint(0, 40), random.randint(0, 20)),
        )
        text_x = (
            sw // 2
            - scare_text.get_width() // 2
            + random.randint(-12 - lvl * 3, 12 + lvl * 3)
        )
        text_y = 30 + random.randint(-8 - lvl * 2, 8 + lvl * 2)
        # More shadow copies at higher levels (ghosting effect)
        for g in range(min(lvl, 4)):
            ghost = scare_font.render(msg, True, (80, 0, 0))
            gx = text_x + random.randint(-10 - g * 3, 10 + g * 3)
            gy = text_y + random.randint(-5 - g * 2, 5 + g * 2)
            surface.blit(ghost, (gx, gy))
        surface.blit(scare_text, (text_x, text_y))

    # Bottom text (gets more ominous)
    if frame > 15:
        sub_font = pygame.font.Font(None, max(24, size // 5))
        if lvl <= 2:
            sub_msg = "IT WAS IN THE CLOSET THE WHOLE TIME..."
        elif lvl <= 4:
            sub_msg = "IT REMEMBERS YOU FROM LAST TIME..."
        else:
            sub_msg = "IT HAS ALWAYS BEEN HERE. IT WILL ALWAYS BE HERE."
        sub_text = sub_font.render(sub_msg, True, (255, 80, 80))
        sub_x = sw // 2 - sub_text.get_width() // 2 + random.randint(-6, 6)
        sub_y = sh - 70 + random.randint(-4, 4)
        surface.blit(sub_text, (sub_x, sub_y))

    # === LEVEL 2+: SCARE COUNTER (reminds you how many times) ===
    if lvl >= 2 and frame > 30:
        count_font = pygame.font.Font(None, 22)
        count_text = count_font.render(
            f"scare #{lvl}",
            True,
            (120, 0, 0),
        )
        surface.blit(count_text, (sw - count_text.get_width() - 10, sh - 30))

    # === GLITCH EFFECT (way more tears at higher levels) ===
    if frame > 10 and frame % max(1, 3 - lvl // 2) == 0:
        num_tears = random.randint(2 + lvl, int(6 * glitch_mult))
        for _ in range(num_tears):
            tear_y = random.randint(0, sh)
            tear_h = random.randint(2, max(3, int(8 * glitch_mult)))
            tear_offset = random.randint(int(-30 * glitch_mult), int(30 * glitch_mult))
            if 0 < tear_y < sh - tear_h:
                strip = surface.subsurface((0, tear_y, sw, tear_h)).copy()
                surface.blit(strip, (tear_offset, tear_y))

    # === LEVEL 3+: SCREEN INVERSION FLICKER ===
    if lvl >= 3 and frame % (12 - lvl) == 0:
        inv_surf = pygame.Surface((sw, sh))
        inv_surf.fill((255, 255, 255))
        inv_surf.set_alpha(random.randint(20, 60 + lvl * 10))
        surface.blit(inv_surf, (0, 0), special_flags=pygame.BLEND_SUB)

    # === LEVEL 5+: MULTIPLE FACES (smaller faces in the corners!) ===
    if lvl >= 5 and frame > 20:
        mini_size = size // 4
        corners = [(80, 80), (sw - 80, 80), (80, sh - 80), (sw - 80, sh - 80)]
        for corner_x, corner_y in corners:
            if random.random() < 0.7:  # flicker in and out
                me_size = mini_size // 5
                me_spacing = mini_size // 4
                pygame.draw.circle(
                    surface, (200, 0, 0), (corner_x - me_spacing, corner_y), me_size
                )
                pygame.draw.circle(
                    surface, (0, 0, 0), (corner_x - me_spacing, corner_y), me_size // 3
                )
                pygame.draw.circle(
                    surface, (200, 0, 0), (corner_x + me_spacing, corner_y), me_size
                )
                pygame.draw.circle(
                    surface, (0, 0, 0), (corner_x + me_spacing, corner_y), me_size // 3
                )
                pygame.draw.ellipse(
                    surface,
                    (30, 0, 0),
                    (
                        corner_x - mini_size // 3,
                        corner_y + me_size + 2,
                        mini_size * 2 // 3,
                        mini_size // 3,
                    ),
                )

    # === RED VIGNETTE ===
    vig_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    vig_step = max(4, 8 - lvl)
    for ring in range(0, max(sw, sh), vig_step):
        alpha = min(200 + lvl * 10, ring * (200 + lvl * 15) // max(sw, sh))
        alpha = min(255, alpha)
        pygame.draw.rect(
            vig_surf,
            (0, 0, 0, alpha),
            (ring // 2, ring // 2, sw - ring, sh - ring),
            max(2, vig_step - 1),
        )
    surface.blit(vig_surf, (0, 0))

    # === FADE OUT AT THE END ===
    total_duration = JUMPSCARE_DURATION + lvl * 60
    fade_start = total_duration - 20
    if frame > fade_start:
        fade_out = (frame - fade_start) / 20.0
        flash_surf = pygame.Surface((sw, sh))
        flash_surf.fill((0, 0, 0))
        flash_surf.set_alpha(min(255, int(fade_out * 255)))
        surface.blit(flash_surf, (0, 0))
