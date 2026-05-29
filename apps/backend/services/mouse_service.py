"""
Human-like mouse movement — moves cursor pixel by pixel with
natural curves, slight randomness, and variable speed.
"""
import pyautogui
import random
import math
import time


def human_move(target_x: int, target_y: int, duration: float = 0.6):
    """
    Move mouse to target with human-like motion.
    Uses bezier curve with random control points for natural path.
    """
    start_x, start_y = pyautogui.position()

    # Distance determines duration
    dist = math.hypot(target_x - start_x, target_y - start_y)
    if dist < 10:
        # Very close — just jump
        pyautogui.moveTo(target_x, target_y)
        return

    # Scale duration by distance
    duration = max(0.3, min(1.2, dist / 1500))

    # Generate bezier control points (creates curve)
    # Add randomness so it doesn't look robotic
    cp1_x = start_x + (target_x - start_x) * 0.3 + random.randint(-40, 40)
    cp1_y = start_y + (target_y - start_y) * 0.3 + random.randint(-40, 40)
    cp2_x = start_x + (target_x - start_x) * 0.7 + random.randint(-30, 30)
    cp2_y = start_y + (target_y - start_y) * 0.7 + random.randint(-30, 30)

    # Number of steps based on distance
    steps = max(20, int(dist / 8))

    # Generate points along bezier curve
    points = []
    for i in range(steps + 1):
        t = i / steps

        # Cubic bezier formula
        x = (1-t)**3 * start_x + 3*(1-t)**2*t * cp1_x + 3*(1-t)*t**2 * cp2_x + t**3 * target_x
        y = (1-t)**3 * start_y + 3*(1-t)**2*t * cp1_y + 3*(1-t)*t**2 * cp2_y + t**3 * target_y

        # Add micro-jitter (human hands shake slightly)
        if 0.1 < t < 0.9:
            x += random.uniform(-1.5, 1.5)
            y += random.uniform(-1.5, 1.5)

        points.append((int(x), int(y)))

    # Move through points with variable speed
    # Slow at start, fast in middle, slow at end (ease-in-out)
    step_delay = duration / steps

    for i, (px, py) in enumerate(points):
        # Ease-in-out timing
        t = i / steps
        speed_factor = 1.0 - 0.6 * math.sin(t * math.pi)  # Slower at edges
        actual_delay = step_delay * speed_factor

        pyautogui.moveTo(px, py, _pause=False)
        time.sleep(actual_delay)

    # Final precise move to exact target
    pyautogui.moveTo(target_x, target_y, _pause=False)


def human_click(x: int, y: int):
    """Move to target like a human, then click."""
    human_move(x, y)
    # Small pause before click (human reaction)
    time.sleep(random.uniform(0.05, 0.12))
    pyautogui.click(_pause=False)
    # Small pause after click
    time.sleep(random.uniform(0.08, 0.15))
