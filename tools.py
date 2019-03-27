import re
from encode import bytes_to_hex, hex_to_bytes


class PaddingError(Exception):
    def __init__(self, msg):
        self.msg = msg


def xor_hex(a, b):
    return bytes_to_hex(xor_bytes(hex_to_bytes(a), hex_to_bytes(b)))


def xor_bytes(a, b):
    """ calculates the xor of 2 bytestrings"""
    return bytes([b1 ^ b2 for b1, b2 in zip(a, b)])


def arrange_blocks_hex(cipher_hex, blocksize):
    blocks = [b'']*blocksize
    # split hex string into blocks of 2
    hex_split = re.findall(b'..', cipher_hex)
    for i, byte in enumerate(hex_split):
        blocks[i % blocksize] += byte
    return list(blocks)


def arrange_blocks(cipher_bytes, blocksize):
    blocks = split_blocks(cipher_bytes, blocksize)
    return list(zip(*blocks))


def split_blocks(cipher_bytes, blocksize):
    blocks = []
    for i in range(0, len(cipher_bytes), blocksize):
        blocks.append(cipher_bytes[i:i+blocksize])
    return blocks


def find_diff_block(a, b, blocksize):
    """given 2 bytestrings and a bs finds index of first block where
    a and b differ. Else returns None"""
    a_list = split_blocks(a, blocksize)
    b_list = split_blocks(b, blocksize)
    for i, b in enumerate(zip(a_list, b_list)):
        if b[0] != b[1]:
            return i
    return None


def get_pref_len(func, blocksize):
    base_block = func(b'C')
    comp_a = func(b'A')
    comp_b = func(b'B')
    ind_a = find_diff_block(base_block, comp_a, blocksize)
    ind_b = find_diff_block(base_block, comp_b, blocksize)
    first_b = min(ind_a, ind_b)
    for i in range(blocksize):
        static = b'c'*i
        a = func(static+b'A')
        b = func(static+b'B')
        index = find_diff_block(a, b, blocksize)
        if index > first_b:
            return (first_b + 1) * blocksize - i
    return first_b * blocksize


def pkcs7_padding(bytes_, blocksize):
    n_pad = blocksize - len(bytes_) % blocksize
    if n_pad == 0:
        n_pad = blocksize
    padding = n_pad*bytes([n_pad])
    return bytes_ + padding


def pkcs7_depad(bytes_, blocksize):
    last_b = bytes_[-1]
    if last_b > blocksize or len(bytes_) % blocksize != 0 or last_b == 0:
        raise PaddingError("Invalid PKCS #7 Padding.")
    for elem in bytes_[-last_b:]:
        if elem != last_b:
            raise PaddingError("Invalid PKCS #7 Padding.")
    return bytes_[:-last_b]


if __name__ == "__main__":
    pass
