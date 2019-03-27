import tools


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


def cbc_po_block(oracle, prev_c_block, target_c_block):
    """ decrypts a block via cbc paddingcoracle """
    blocksize = len(target_c_block)
    plain = b''
    for i in range(1, blocksize+1):
        pre = prev_c_block[:-i]
        post = tools.xor_bytes(bytes([i]*(i-1)), prev_c_block[-i+1:])
        post = tools.xor_bytes(post, plain[-i+1:])
        for guess in range(0, 256):
            x = bytes([guess ^ prev_c_block[-i] ^ i])  # guess xor prev_cipher xor padding
            mod_block = pre + x + post
            # print("oracle: ", mod_block, target_c_block)
            if oracle(mod_block+target_c_block):
                # TODO maybe check for false pos by modifying last byte of pre
                if i < blocksize:
                    mod_block = pre[:-1]+bytes([pre[-1]+1])+x+post
                    if oracle(mod_block+target_c_block):
                        plain = bytes([guess]) + plain
                else:
                    plain = bytes([guess]) + plain
    return plain


def cbc_padding_oracle(oracle, ciphertext, blocksize, iv=None):
    if iv is None:
        iv = bytes(blocksize)
    c_blocks = tools.split_blocks(ciphertext, blocksize)
    p_blocks = []
    for i, c_block in enumerate(c_blocks):
        if i == 0:
            pre = iv
        else:
            pre = c_blocks[i-1]
        p_blocks.append(cbc_po_block(oracle, pre, c_block))
    return b''.join(p_blocks)


if __name__ == '__main__':
    pass
