import random
import aes


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


key = get_rand_bytes()


def encrypt(inp):
    try:
        inp = inp.encode()
    except AttributeError:
        pass
    inp = inp.replace(b';', b'%3b').replace(b'=', b'%3d')
    pref = b"comment1=cooking%20MCs;userdata="
    postf = b";comment2=%20like%20a%20pound%20of%20bacon"
    plain = pref + inp + postf
    return aes.ctr_transform(plain, key, 0)


def is_admin(ciphertext):
    plaintext = aes.ctr_transform(ciphertext, key, 0)
    return b';admin=true;' in plaintext


def main():
    pass


if __name__ == '__main__':
    main()
