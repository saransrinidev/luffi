"""
Human-like mouse movement — moves cursor pixel by pixel with
natural curves, slight randomness, and variable speed.

Tuned for SLOWER, more human-like pacing.
"""
import pyautogui
import random
import math
import time


def human_move(target_x: int, target_y: int, duration: float = None):
    """
    Move mouse to target with human-like motion.
    Uses bezier curve with random control points for natural path.
    Slower pacing to mimic real human hand movement.
    """
    start_x, start_y = pyautogui.position()

    # Distance determines duration
    dist = math.hypot(target_x - start_x, target_y - start_y)
    if dist < 8:
        pyautogui.moveTo(target_x, target_y, _pause=False)
        return

    # Slower: scale duration by distance (longer than before)
    if duration is None:
        duration = max(0.7, min(2.2, dist / 700))

    # Bezier control points with randomness (curved path)
    cp1_x = start_x + (target_x - start_x) * 0.3 + random.randint(-60, 60)
    cp1_y = start_y + (target_y - start_y) * 0.3 + random.randint(-60, 60)
    cp2_x = start_x + (target_x - start_x) * 0.7 + random.randint(-45, 45)
    cp2_y = start_y + (target_y - start_y) * 0.7 + random.randint(-45, 45)

    # More steps = smoother, slower visible movement
    steps = max(40, int(dist / 4))

    points = []
    for i in range(steps + 1):
        t = i / steps
        x = (1-t)**3 * start_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * target_x
        y = (1-t)**3 * start_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * target_y

        # Micro-jitter (hand tremor)
        if 0.1 < t < 0.9:
            x += random.uniform(-2.0, 2.0)
            y += random.uniform(-2.0, 2.0)

        points.append((int(x), int(y)))

    step_delay = duration / steps

    for i, (px, py) in enumerate(points):
        # Ease-in-out — slow at start and end
        t = i / steps
        speed_factor = 1.0 - 0.55 * math.sin(t * math.pi)
        actual_delay = step_delay * speed_factor

        # Occasional tiny hesitation mid-movement (very human)
        if random.random() < 0.03:
            actual_delay += random.uniform(0.02, 0.06)

        pyautogui.moveTo(px, py, _pause=False)
        time.sleep(actual_delay)

    pyautogui.moveTo(target_x, target_y, _pause=False)


def human_click(x: int, y: int):
    """Move to target like a human, then click with natural pauses."""
    human_move(x, y)
    # Pause before click (human reaction / aiming)
    time.sleep(random.uniform(0.15, 0.35))
    pyautogui.click(_pause=False)
    # Pause after click (settle)
    time.sleep(random.uniform(0.2, 0.45))


def human_type(text: str):
    """Type text with human-like variable speed and occasional pauses."""
    for i, char in enumerate(text):
        pyautogui.typewrite(char, _pause=False)

        # Variable per-character delay (humans don't type at constant speed)
        delay = random.uniform(0.06, 0.18)

        # Longer pause after spaces and punctuation (word boundaries)
        if char in " .,!?":
            delay += random.uniform(0.08, 0.2)

        # Occasional "thinking" pause
        if random.random() < 0.05:
            delay += random.uniform(0.2, 0.5)

        time.sleep(delay)
