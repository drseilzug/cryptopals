from analyse import guess_keysize
from encode import b64_to_hex, bytes_to_hex, hex_to_bytes
from tools import xor_hex, arrange_blocks
from char_xor import analyze_xor_char


def xor_against_key(inp_hex, key):
    """"takes hex sting and char and returns bytestrings"""
    div, mod = divmod(len(inp_hex)//2, len(key))
    full_key = key*div+key[:mod]
    h_key = full_key.hex()
    return xor_hex(inp_hex, h_key)
    # return hex_to_bytes(h_out)


def encrypt_rep_key_xor(plain, key):
    return xor_against_key(bytes_to_hex(plain), key)


def decrypt_rep_key_xor(hexstring, key):
    return hex_to_bytes(xor_against_key(hexstring, key))


def analyze_rep_key_xor(cipher_hex, blocksize, show_n=1):
    blocks = arrange_blocks(bytes.fromhex(cipher_hex), blocksize)
    best_guesses = []
    for block in blocks:
        result = analyze_xor_char(block, show_n)
        # result -> [(score, char, current)][0] -> (,,)
        best_guesses.append(result)
    return best_guesses


def get_Key_from_results(results):
    """ only gets the keys from the best guesses"""
    key = b''
    for elem in results:
        key += elem[0][1]
    return key


if __name__ == "__main__":
    data_b64 = ""
    with open('6.txt', 'r') as f:
        data_b64 = f.read()
    data_hex = b64_to_hex(data_b64)
    # plain = decrypt_rep_key_xor(data_hex, 'Terminator X: Bring the noise')

    # guesses = guess_keysize(data_hex)
    # print(guesses)

    # for size in size_guesses:
    res = analyze_rep_key_xor(data_hex, 29)  # size)
    print("Results for size ", "29")
    print(res)
    print("Key: ", get_Key_from_results(res))
    # 29 was actually right (???) found it since 58 also works obviously
    # key = 'Terminator X: Bring the noise'
