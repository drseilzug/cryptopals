import aes
import analyse
import tools


def parse_postargs(arg_string):
    fields = arg_string.split('&')
    profile = dict()
    for f in fields:
        k, v = f.split('=')
        profile[k] = v
    return profile


key = aes.get_rand_key()


def profile_for(email):
    try:
        email = email.encode()
    except AttributeError:
        pass
    email = email.replace(b"&", b"").replace(b"+", b"")
    profile = b'email=' + email + b'&uid=10&role=user'
    return aes.encrypt_ecb_aes(profile, key)


def dec_profile(profile):
    return aes.decrypt_ecb_aes(profile, key)


def main():
    blocksize, padding = analyse.test_blocksize(profile_for)
    print("Blocksize found: ", blocksize)
    print("Paddingbytes: ", padding)
    print("ECB detected: ", analyse.test_ecb(profile_for, blocksize))
    pref_length = tools.get_pref_len(profile_for, blocksize)
    print("prefix_length: ", pref_length)
    print("constructing fake end block")
    fill = b'A'*(blocksize-(pref_length % blocksize))
    fake_end_plain = tools.pkcs7_padding(b'admin', blocksize)
    target_block = (pref_length//blocksize)+1
    end = tools.split_blocks(profile_for(fill+fake_end_plain), blocksize)[target_block]
    dec_end = dec_profile(end)
    print("test decoding generated fake end block: ", dec_end)
    if dec_end == b'admin':
        print("SUCCESS!")
    print("generating aligned main cipherblocks")
    main_fill = b'A'*(padding+len(b"user"))
    main_blocks = tools.split_blocks(profile_for(main_fill), blocksize)[:-1]
    main_ciphertext = b''.join(main_blocks)
    print("constructing payload")
    payload = main_ciphertext+end
    print("Testdecoding payload: ", dec_profile(payload))


if __name__ == '__main__':
    main()
