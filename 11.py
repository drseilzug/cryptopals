import aes
import random
from tools import split_blocks


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


def encryption_oracle(inp):
    begin = get_rand_bytes(random.randint(5, 10))
    end = get_rand_bytes(random.randint(5, 10))
    key = get_rand_bytes(16)
    data = begin + inp + end
    if random.randint(0, 1):
        return (aes.encrypt_ecb_aes(data, key), 0)
    else:
        return (aes.cbc_encrypt(data, key, get_rand_bytes(16)), 1)


def main():
    inp = bytes(70)
    data_set = []
    for _ in range(10):
        enc = ''
        data, answer = encryption_oracle(inp)
        reps = len(split_blocks(data, 16)) - len(set(split_blocks(data, 16)))
        if answer == 0:
            enc = 'ECB'
        else:
            enc = 'CBC'
        data_set.append((enc, reps))
    for element in data_set:
        print(element)


if __name__ == '__main__':
    main()
