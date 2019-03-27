import analyse
import tools
import random
import aes


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


key = get_rand_bytes()
iv = get_rand_bytes()


def encrypt(inp):
    try:
        inp = inp.encode()
    except AttributeError:
        pass
    inp = inp.replace(b';', b'%3b').replace(b'=', b'%3d')
    pref = b"comment1=cooking%20MCs;userdata="
    postf = b";comment2=%20like%20a%20pound%20of%20bacon"
    plain = pref + inp + postf
    return aes.cbc_encrypt(plain, key, iv)


def is_admin(ciphertext):
    plaintext = aes.cbc_decrypt(ciphertext, key, iv)
    return b';admin=true;' in plaintext


def cbc_byteflip(func, target_plain, base_plain, blocksize, prefix_length=0):
    if max(len(target_plain), len(base_plain)) > blocksize:
        raise ValueError("Attack does not support targets larger than blocksize")
    elif len(target_plain) != len(base_plain):
        raise ValueError("target_plain and base_plain have to be of equal length")
    offset = 0
    if prefix_length % blocksize != 0:
        offset = blocksize - prefix_length % blocksize
    padd_start = b'A' * offset + b'A' * blocksize
    base_cipher_blocks = tools.split_blocks(func(padd_start + base_plain), blocksize)
    target_index = (prefix_length + offset) // blocksize
    target_block = base_cipher_blocks[target_index]
    padd_block = bytes(blocksize - len(target_plain))
    base_plain += padd_block
    target_plain += padd_block
    # generate modified cipher_block
    diff = tools.xor_bytes(target_plain, base_plain)
    new_block = tools.xor_bytes(diff, target_block)
    mod_cipher_blocks = base_cipher_blocks[:]
    mod_cipher_blocks[target_index] = new_block
    return b''.join(mod_cipher_blocks)


def main():
    blocksize, _ = analyse.test_blocksize(encrypt)
    print("Found blocksize: ", blocksize)
    pref_len = tools.get_pref_len(encrypt, blocksize)
    print("prefix length:", pref_len)
    # offset = 0
    base_plain = b'XadminXtrue'
    target_plain = b';admin=true'
    print("Generate modified Cipertext from: ", base_plain, target_plain)
    payload = cbc_byteflip(encrypt, target_plain, base_plain, blocksize, pref_len)
    print("Test payload: ", is_admin(payload))


if __name__ == '__main__':
    main()
