import base64
import random
from Crypto.Cipher import AES
from tools import split_blocks, xor_bytes, pkcs7_padding, pkcs7_depad


def get_rand_key(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


def decrypt_ecb_aes(ciphertext, key, padding=True):
    cipher = AES.new(key, AES.MODE_ECB)
    plain = cipher.decrypt(ciphertext)
    if padding:
        plain = pkcs7_depad(plain, 16)
    return plain


def encrypt_ecb_aes(plaintext, key, padding=True):
    ciper = AES.new(key, AES.MODE_ECB)
    if padding:
        plaintext = pkcs7_padding(plaintext, 16)
    ciphertext = ciper.encrypt(plaintext)
    return ciphertext


def cbc_decrypt_block(c_previous, pre_plain_current):
    """
    in
    :c_previous -- the last cipherblock (or IV if first block)
    :pre_p_current -- the decrypted current cipherblock
    out
    :p _current
    """
    return xor_bytes(c_previous, pre_plain_current)


def cbc_encrypt_block(c_previous, p_current, key):
    """
    in
    :key -- key to encrypt the block
    :c_previous -- the last cipher_block
    :p_current -- the plain block to eb encrypted
    out
    :c_current -- the encrypted block
    """
    return encrypt_ecb_aes(xor_bytes(c_previous, p_current), key, False)


def cbc_decrypt(ciphertext, key, iv=bytes(16)):
    """
    Currently has AES-128 hardcoded
    default iv is 16 zerobytes
    """
    blocksize = len(iv)
    pre_plain = decrypt_ecb_aes(ciphertext, key, False)
    c_blocks = [iv]
    c_blocks += split_blocks(ciphertext, blocksize)
    pp_blocks = split_blocks(pre_plain, blocksize)
    plaintext = b''
    for i, block in enumerate(pp_blocks):
        plaintext += cbc_decrypt_block(c_blocks[i], block)
    plaintext = pkcs7_depad(plaintext, blocksize)
    return plaintext


def cbc_encrypt(plaintext, key, iv=bytes(16)):
    """
    hardcoded to use aes-128, and pkcs7_padding
    default iv is 16 zerobytes
    """
    try:
        plaintext = plaintext.encode()
    except AttributeError:
        pass
    blocksize = len(iv)
    plain_padded = pkcs7_padding(plaintext, blocksize)
    plain_blocks = split_blocks(plain_padded, blocksize)
    cipher_blocks = [iv]
    for block in plain_blocks:
        cipher_blocks.append(cbc_encrypt_block(cipher_blocks[-1], block, key))
    return b''.join(cipher_blocks[1:])  # return ciphertext without IV


def ctr_aes128_keystream_gen(key, nonce, counter_start=0):
    """ a generator that returns 16 bytes keystream on each next call"""
    counter = counter_start
    while True:
        pre_keyblock = nonce.to_bytes(8, 'little') + counter.to_bytes(8, 'little')
        keyblock = encrypt_ecb_aes(pre_keyblock, key, False)
        yield keyblock
        counter += 1


def ctr_transform(plain, key, nonce):
    plain_blocks = split_blocks(plain, 16)
    cipher_blocks = []
    keystream = ctr_aes128_keystream_gen(key, nonce)
    for block in plain_blocks:
        ks_block = next(keystream)
        cipher_blocks.append(xor_bytes(ks_block, block))
    return b''.join(cipher_blocks)


if __name__ == '__main__':
    cipher_b64 = ""
    with open('10.txt', 'r') as f:
        cipher_b64 = f.read()
    cipher_bytes = base64.b64decode(cipher_b64)
    iv = bytes(16)  # 16 zero bytes
    key = b'YELLOW SUBMARINE'
    plain = cbc_decrypt(cipher_bytes, key, iv)
    print(plain[-20:], "OUT dec of original")
    c_2 = cbc_encrypt(plain, key, iv)
    p_2 = cbc_decrypt(c_2, key, iv)
    print(p_2[-20:], "OUT 2nd decr")
