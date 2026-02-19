import time
import os
import sys
from unittest.mock import MagicMock

# Mock dependencies before import
sys.modules['requests'] = MagicMock()
sys.modules['dotenv'] = MagicMock()

# Add scripts directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import minecraft_bot
# Override PROPERTIES_FILE to point to local dummy file
minecraft_bot.PROPERTIES_FILE = 'server.properties'

from minecraft_bot import read_property, read_all_properties

def create_dummy_properties():
    with open('server.properties', 'w') as f:
        for i in range(100):
            f.write(f"key{i}=value{i}\n")
        f.write("pvp=true\n")
        f.write("allow-flight=false\n")
        f.write("allow-nether=true\n")
        f.write("max-players=20\n")
        f.write("view-distance=10\n")

def benchmark_multiple_reads_naive(n=1000):
    # This function simulates the behavior of calling read_property multiple times
    # In the optimized version, read_property opens the file every time (which is slow for single calls but correct)
    # The optimization is in how the caller uses it, or if read_property cached it (which we didn't implement fully, we rely on read_all_properties for bulk access)

    # Wait, the current implementation of read_property calls read_all_properties which opens the file.
    # So calling read_property 5 times opens the file 5 times.
    # The optimization is that get_properties_keyboard calls read_all_properties ONCE.

    start = time.time()
    for _ in range(n):
        # Simulating unoptimized usage: 5 separate calls
        read_property('pvp')
        read_property('allow-flight')
        read_property('allow-nether')
        read_property('max-players')
        read_property('view-distance')
    end = time.time()
    return end - start

def benchmark_multiple_reads_optimized(n=1000):
    start = time.time()
    for _ in range(n):
        # Simulating optimized usage: 1 call to get all properties
        props = read_all_properties()
        props.get('pvp')
        props.get('allow-flight')
        props.get('allow-nether')
        props.get('max-players')
        props.get('view-distance')
    end = time.time()
    return end - start

if __name__ == "__main__":
    create_dummy_properties()
    n = 1000
    print(f"Benchmarking (n={n})...")

    t_naive = benchmark_multiple_reads_naive(n)
    print(f"Naive (5 calls via read_property): {t_naive:.4f}s")

    t_opt = benchmark_multiple_reads_optimized(n)
    print(f"Optimized (1 call via read_all_properties): {t_opt:.4f}s")

    if t_opt > 0:
        print(f"Speedup: {t_naive / t_opt:.2f}x")

    if os.path.exists('server.properties'):
        os.remove('server.properties')
