import frequency
import copy
from tools import xor_bytes
from math import inf
from string import printable


def hamming_hex(hex_a, hex_b):
    """takes 2 hex representations and calculaes the hamming distance"""
    return hamming(bytes.fromhex(hex_a), bytes.fromhex(hex_b))


def hamming(bytes_a, bytes_b):
    """takes 2 bytestrings and calculates the hamming distance"""
    for inp in [bytes_a, bytes_b]:
        try:
            inp = inp.encode()
        except AttributeError:
            pass
    dist = 0
    diff = xor_bytes(bytes_a, bytes_b)
    for char in diff:
        dist += str(bin(char)).count('1')
    return dist


def guess_keysize(cyper_hex, max_range=40, max_deepth=0):
    """
    Tries to guess keysize by claculating the hamming distance between blocks.
    max_deepth specifies max number of blocks considered.
    (0 means use as many as possible)
    """
    cipher_bytes = bytes.fromhex(cyper_hex)
    length = len(cyper_hex)
    norm_dists_per_key = []
    # iterate over possible key lenghts
    for key_l in range(2, max_range):
        norm_dists = []
        if max_deepth > 0:
            block_count = min(max_deepth//key_l, length//(key_l*2))
        else:
            block_count = length//(key_l*2)
        for index in range(block_count//key_l):
            i = index*key_l
            block_a = cipher_bytes[i:i+key_l]
            block_b = cipher_bytes[i+key_l:i+2*key_l]
            dist = hamming(block_a, block_b)
            norm_dists.append(dist/key_l)
        norm_dists_per_key.append((sum(norm_dists)/len(norm_dists), key_l))
    norm_dists_per_key.sort()
    return norm_dists_per_key


def score_string_chi(inp):
    """
    asigns a score to to the input bytestring by comparing the distribution
    of characters (letters and spaces) to the average distribution in
    english using chi-squared.
    lower score means better match
    only use for long texts
    (want to expect at least about 5 of the rares characters)
    """
    exp_dist = copy.deepcopy(frequency.frequency)
    length = len(inp)
    for key in exp_dist:
        exp_dist[key] *= length
    try:
        inp = inp.encode()
    except AttributeError:
        pass
    dist = dict.fromkeys(exp_dist.keys(), 0)
    for char in inp.lower():
        if chr(char) not in printable:
            return inf
        if char in dist:
            dist[char] += 1
    score = 0
    for key in exp_dist:
        score += (dist[key]-exp_dist[key])**2/exp_dist[key]
    return score


def score_string(inp):
    """ Naive string scoring method """
    freq = copy.deepcopy(frequency.frequency)
    score = 0
    for char in inp.lower():
        if char in freq:
            score += freq[char]
    return score


def test_blocksize(func):
    """tests a function that does func(plaintext)=cypertext
    to get (blocksize, padding)"""
    inputsize = 0
    base_size = len(func(b''))
    current_size = len(func(b''))
    # appends bytes until new block is returned
    while current_size == base_size:
        inputsize += 1
        current_size = len(func(b'A'*inputsize))
    blocksize = current_size-base_size
    return (blocksize, inputsize)


def test_ecb(func, blocksize):
    """tests a function that does func(plaintext)=ciphertext against ecb
    by repitition. can handle arbitrary pre/postfixes"""
    u_blockcount = set()
    for i in range(3, 5):
        u_blockcount.add(len(set(func(b'A'*i*blocksize))))
    return len(u_blockcount) == 1


if __name__ == '__main__':
    score = score_string(b'the quick brown fox jumps over some')
    print(score)
