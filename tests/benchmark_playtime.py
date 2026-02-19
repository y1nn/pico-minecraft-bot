import timeit
import random
import sys
import os
from unittest.mock import MagicMock

# Ensure scripts can be imported
if os.getcwd() not in sys.path:
    sys.path.append(os.getcwd())

# Mock dependencies
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

# Import the actual function to verify it works (optional)
# from scripts.minecraft_bot import format_playtime_message

def generate_data(n=1000):
    return [('Player'+str(i), random.random()*100) for i in range(n)]

def bad_concat_loop(data):
    """Simulates the inefficient pattern: formatting N items with +=."""
    msg = "🏆 *Top Playtime:*\n"
    for i, (name, hours) in enumerate(data, 1):
        msg += f"{i}. 👤 *{name}:* `{hours:.1f} hours`\n"
    return msg

def good_join_loop(data):
    """Simulates the efficient pattern: formatting N items with join."""
    msg_parts = ["🏆 *Top Playtime:*\n"]
    for i, (name, hours) in enumerate(data, 1):
        msg_parts.append(f"{i}. 👤 *{name}:* `{hours:.1f} hours`\n")
    return "".join(msg_parts)

if __name__ == "__main__":
    print("=== Benchmark: String Concatenation vs List Join ===")
    print("Rationale: Repeatedly concatenating strings in a loop is O(N^2).")
    print("           Using list accumulation + join is O(N).")
    print("           While the current leaderboard only shows 5 items, using the efficient")
    print("           pattern is important for scalability and code health.\n")

    N = 10000
    data = generate_data(N)

    print(f"Benchmarking with N={N} items...")

    t_bad = timeit.timeit(lambda: bad_concat_loop(data), number=50)
    t_good = timeit.timeit(lambda: good_join_loop(data), number=50)

    print(f"Bad (Concatenation): {t_bad:.4f}s")
    print(f"Good (List Join):   {t_good:.4f}s")

    if t_good > 0:
        print(f"Speedup: {t_bad/t_good:.2f}x")
