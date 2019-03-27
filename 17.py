import aes
import tools
import random
import base64
import attacks


key = aes.get_rand_key()
strings = ['MDAwMDAwTm93IHRoYXQgdGhlIHBhcnR5IGlzIGp1bXBpbmc=',
           'MDAwMDAxV2l0aCB0aGUgYmFzcyBraWNrZWQgaW4gYW5kIHRoZSBWZWdhJ3MgYXJlIHB1bXBpbic=',
           'MDAwMDAyUXVpY2sgdG8gdGhlIHBvaW50LCB0byB0aGUgcG9pbnQsIG5vIGZha2luZw==',
           'MDAwMDAzQ29va2luZyBNQydzIGxpa2UgYSBwb3VuZCBvZiBiYWNvbg==',
           'MDAwMDA0QnVybmluZyAnZW0sIGlmIHlvdSBhaW4ndCBxdWljayBhbmQgbmltYmxl',
           'MDAwMDA1SSBnbyBjcmF6eSB3aGVuIEkgaGVhciBhIGN5bWJhbA==',
           'MDAwMDA2QW5kIGEgaGlnaCBoYXQgd2l0aCBhIHNvdXBlZCB1cCB0ZW1wbw==',
           'MDAwMDA3SSdtIG9uIGEgcm9sbCwgaXQncyB0aW1lIHRvIGdvIHNvbG8=',
           'MDAwMDA4b2xsaW4nIGluIG15IGZpdmUgcG9pbnQgb2g=',
           'MDAwMDA5aXRoIG15IHJhZy10b3AgZG93biBzbyBteSBoYWlyIGNhbiBibG93']


def encrypt():
    iv = aes.get_rand_key(16)
    plain = base64.b64decode(strings[random.randint(0, 9)])
    ciphertext = aes.cbc_encrypt(plain, key, iv)
    return ciphertext, iv


def decrypt(cipertext, iv):
    return aes.cbc_decrypt(cipertext, key, iv)


def oracle(ciphertext):
    try:
        aes.cbc_decrypt(ciphertext, key)
    except tools.PaddingError:
        return False
    else:
        return True


def main():
    print('Aquire ciphertext.')
    cipher, iv = encrypt()
    print("Solution: ", tools.pkcs7_padding(decrypt(cipher, iv), 16))
    blocksize = len(iv)
    # a, b = tools.split_blocks(cipher, blocksize)[-2:]
    # plain = attacks.cbc_po_block(oracle, a, b)
    plain = attacks.cbc_padding_oracle(oracle, cipher, blocksize, iv)
    print("Plaintext: ", plain)


if __name__ == '__main__':
    main()
