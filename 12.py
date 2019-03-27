import base64
import random
import aes
import analyse


def get_rand_bytes(size=16):
    return bytes([random.randint(0, 255) for _ in range(size)])


sec_b64 = """Um9sbGluJyBpbiBteSA1LjAKV2l0aCBteSByYWctdG9wIGRvd24gc28gbXkg
aGFpciBjYW4gYmxvdwpUaGUgZ2lybGllcyBvbiBzdGFuZGJ5IHdhdmluZyBq
dXN0IHRvIHNheSBoaQpEaWQgeW91IHN0b3A/IE5vLCBJIGp1c3QgZHJvdmUg
YnkK"""
secret = base64.b64decode(sec_b64)
key = get_rand_bytes(16)


def encryption_oracle(inp):
    end = secret
    data = inp + end
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


def main():
    blocksize, padding = analyse.test_blocksize(encryption_oracle)
    print("Blocksize found: ", blocksize)
    print("Paddingbytes: ", padding)
    print("ECB detected: ", analyse.test_ecb(encryption_oracle, blocksize))
    brute_ecb(encryption_oracle, blocksize, padding)


if __name__ == '__main__':
    main()
