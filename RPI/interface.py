import time
import random


def takeImage():
    if random.randint(0, 99) < 50:
        return True, "/images/banapple.jpg", True
    return False, "false", False