from sha1 import Sha1
import random


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


key = get_rand_bytes(16)


def sha1_mac(input):
    return Sha1(key+input).hexdigest()