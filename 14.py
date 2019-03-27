import base64
import random
import aes
import analyse
import tools


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


rand_prefix = get_rand_bytes(random.randint(0, 255))
sec_b64 = """Um9sbGluJyBpbiBteSA1LjAKV2l0aCBteSByYWctdG9wIGRvd24gc28gbXkg
aGFpciBjYW4gYmxvdwpUaGUgZ2lybGllcyBvbiBzdGFuZGJ5IHdhdmluZyBq
dXN0IHRvIHNheSBoaQpEaWQgeW91IHN0b3A/IE5vLCBJIGp1c3QgZHJvdmUg
YnkK"""
secret = base64.b64decode(sec_b64)
key = get_rand_bytes(16)


def encryption_oracle(inp):
    end = secret
    data = rand_prefix + inp + end
    return aes.encrypt_ecb_aes(data, key)


def brute_char(func, ref_block, plainstart):
    blocksize = len(ref_block)
    for n in range(255):
        byte = bytes([n])
        if func(plainstart+byte)[:blocksize] == ref_block:
            return byte


def brute_ecb(func, blocksize, padding):
    plain = bytes(blocksize - 1)
    lenght = len(func(b''))-padding+1
    chars_found = 0
    for _ in range(lenght):
        chars_found_block = chars_found % blocksize
        current_block = chars_found - chars_found_block
        # ref_end = current_block + blocksize - (chars_found % blocksize)
        plainstart = plain[1-blocksize:]  # last bs-1 bytes of found plaintext
        ref_block = func(bytes(blocksize-chars_found_block))[current_block:current_block+blocksize]
        plain += brute_char(func, ref_block, plainstart)
        # yield
        print(plain[blocksize:])
        chars_found += 1
    return plain[blocksize:]


def remove_pref_blocks(func, inp, pref_length, blocksize):
    """wrapper
    takes a func pain --> ciphertext
    padds the input to fill prefix blocks and strip output
    return output as if there was no prefix"""
    padding = bytes(blocksize - pref_length % blocksize)
    padded_out = func(padding+inp)
    block_to_remove = pref_length//blocksize
    if pref_length % blocksize != 0:
        block_to_remove += 1
    stripped_out = tools.split_blocks(padded_out, blocksize)[block_to_remove:]
    return b''.join(stripped_out)


def main():
    blocksize, padding = analyse.test_blocksize(encryption_oracle)
    print("Blocksize found: ", blocksize)
    print("Paddingbytes: ", padding)
    print("ECB detected: ", analyse.test_ecb(encryption_oracle, blocksize))
    pref_len = tools.get_pref_len(encryption_oracle, blocksize)
    print("Determine prefix_length: ", pref_len)
    print("Construct stripped function.")
    print("adjust padding")
    stripped_func = lambda inp: remove_pref_blocks(encryption_oracle, inp, pref_len, blocksize)
    _, padding = analyse.test_blocksize(stripped_func)
    brute_ecb(stripped_func, blocksize, padding)


if __name__ == '__main__':
    main()
