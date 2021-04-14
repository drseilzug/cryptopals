from sha1 import Sha1
import random


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


key = get_rand_bytes(16)


def sha1_mac(input):
    return Sha1(key+input).hexdigest()
print(b"comment1=cooking%20MCs;userdata=foo;comment2=%20like%20a%20pound%20of%20bacon")
print(len(b"comment1=cooking%20MCs;userdata=foo;comment2=%20like%20a%20pound%20of%20bacon"))
print(sha1_mac(b"comment1=cooking%20MCs;userdata=foo;comment2=%20like%20a%20pound%20of%20bacon"))

def validate(message, hash):
    return sha1_mac(message) == hash
