from encode import hex_to_bytes
from tools import xor_bytes
from analyse import score_string


def char_xor(input_bytes, char_byte):
    """ xors each char of input with char_byte. Returns bytestring"""
    for x in [input_bytes, char_byte]:
        try:
            x = x.decode()
        except AttributeError:
            pass
    key = len(input_bytes)*char_byte
    return xor_bytes(input_bytes, key)


def analyze_xor_char(byte_string, show_n=1):
    """Analyzes string against xor with 1 char
    and prints the best show_n results"""
    results = []
    for char in range(256):
        current = char_xor(byte_string, [char])
        score = score_string(current)
        results.append((score, bytes([char]), current))
    results.sort(reverse=True)
    return results[:show_n]


def analyse_xor_char_hex(hex_string, show_n=1):
    return analyze_xor_char(hex_to_bytes(hex_string), show_n)


if __name__ == '__main__':
    # res = analyse_xor_char_hex('1b37373331363f78151b7f2b783431333d78397828372d363c78373e783a393b3736', 3)
    res = analyze_xor_char(bytes.fromhex('1b37373331363f78151b7f2b783431333d78397828372d363c78373e783a393b3736'), 5)
