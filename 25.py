import aes
import base64
from tools import xor_bytes


def get_base_ciphertext():
    ciphertext = b""
    old_key = "YELLOW SUBMARINE"
    global key
    key = aes.get_rand_key(16)
    with open('25.txt', 'r') as f:
        ciphertext = base64.b64decode(f.read())
    plain = aes.decrypt_ecb_aes(ciphertext, old_key)
    return aes.ctr_transform(plain, key, 0)


base_ciphertext = get_base_ciphertext()


def edit(offset, plain_substitute):
    plain = aes.ctr_transform(base_ciphertext, key, 0)
    new_plain = plain[:offset] + plain_substitute + plain[offset+len(plain_substitute):]
    out = aes.ctr_transform(new_plain, key, 0)
    return out


def main():
    length = len(base_ciphertext)
    dummy = bytes(length)
    key_stream = edit(0, dummy)
    solution = xor_bytes(key_stream, base_ciphertext)
    print(solution.decode())


if __name__ == '__main__':
    main()
