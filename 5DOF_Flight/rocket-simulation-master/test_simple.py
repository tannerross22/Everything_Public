#!/usr/bin/env python3
import sys
import traceback

try:
    print("Starting imports...", file=sys.stderr)
    sys.stderr.flush()

    print("Importing Environment...")
    from src.environment import Environment
    print("Success")

    print("Importing Motor...")
    from src.rocketparts.motor import Motor
    print("Success")

    print("Creating Environment...")
    env = Environment(time_increment=0.01)
    print("Success")

    print("Creating Motor...")
    motor = Motor()
    print("Success")

    print("All tests passed!")

except Exception as e:
    print(f"ERROR: {e}", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)
