import sys
import timeit
from unittest.mock import MagicMock

# Mock dependencies before importing the script
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["subprocess"] = MagicMock()

from scripts.minecraft_bot import strip_ansi

def run_benchmark():
    sample_text = "\x1b[31mRed\x1b[0m \x1b[1mBold\x1b[0m \x1b[32mGreen\x1b[0m \x1b[44mBlueBG\x1b[0m Text with some ANSI codes."

    number = 100000
    timer = timeit.Timer(lambda: strip_ansi(sample_text))

    time_taken = timer.timeit(number=number)
    print(f"Executed {number} times.")
    print(f"Total time: {time_taken:.4f} seconds")
    print(f"Average time per call: {time_taken/number*1e6:.4f} microseconds")

if __name__ == "__main__":
    run_benchmark()
