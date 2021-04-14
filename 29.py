from sha1 import Sha1
import random


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


key = get_rand_bytes(16)


def sha1_mac(message):
    return Sha1(key+message).hexdigest()


def validate(message, validation_hash):
    return sha1_mac(message) == validation_hash


if __name__ == "__main__":
    msg = b"comment1=cooking%20MCs;userdata=foo;comment2=%20like%20a%20pound%20of%20bacon"
    mac = sha1_mac(b"comment1=cooking%20MCs;userdata=foo;comment2=%20like%20a%20pound%20of%20bacon")
    print(msg, mac)
    #attack
    ext = Sha1()
    ext.init_extension_hex(mac, 16, msg, b";admin=true")
    new_msg, new_digest = ext.payload()
    print(validate(new_msg, new_digest))
