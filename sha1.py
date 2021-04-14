import struct


class Sha1:
    def __init__(self, message=b''):
        self.h0 = 0x67452301
        self.h1 = 0xEFCDAB89
        self.h2 = 0x98BADCFE
        self.h3 = 0x10325476
        self.h4 = 0xC3D2E1F0

        # sets self.message
        if isinstance(message, str):
            self.message = message.encode()
        else:
            self.message = message

        self.message_p = self.message + self.padd(self.message)
        self.calculate_digest()

    def init_extension(self, bin_digest, prefix_len, orig_message, extension):
        """
        calculates length extension payloads to extend a hash with unknown prefix. (e.g. hash(key|message))

        :param bin_digest: the original digest as a byte string
        :param prefix_len: the length of the unknown prefix in bytes (usually the secret key length)
        :param orig_message: the known part of the original message
        :param extension: the desired content of the extension
        """
        # fill internal state
        self.h0, self.h1, self.h2, self.h3, self.h4 = struct.unpack(">IIIII", bin_digest)
        orig_padding = self.padd(orig_message, prefix_len)
        self.message = orig_message + orig_padding + extension
        # append padding based on full message to extension and setup internal state
        self.message_p = extension + self.padd(self.message, prefix_len)
        self.calculate_digest()

    def init_extension_hex(self, hex_digest, prefix_len, orig_message, extension):
        self.init_extension(bytes.fromhex(hex_digest), prefix_len, orig_message, extension)

    @staticmethod
    def padd(message, prefix_len=0):
        """
        :param message: the message to be padded
        :param prefix_len: modifier to message length in case of unknow prefix in bytes
        :return: padding to be appended
        """
        ml = (len(message) + prefix_len)*8  # bit length of message
        padding = b"\x80"
        # padding to multiple of 64 bytes saving 8 bytes for ml as unsigned long long and 1 byte for x\80 from prev line
        padding += bytes(55 - (ml // 8) % 64)
        padding += struct.pack(">Q", ml % 2**64)
        return padding

    def calculate_digest(self):
        #unpacks to 16 unsigned integers big endian
        chunks = struct.iter_unpack(">16I", self.message_p)
        for chunk in chunks:
            self.process_chunk(chunk)  # updates h0 - h4 accordingly

    @staticmethod
    def left_rotate(word, steps, wordsize=32):
        word <<= steps
        word += word // 2 ** wordsize
        word %= 2 ** wordsize
        return word

    def process_chunk(self, chunk):
        a, b, c, d, e = self.h0, self.h1, self.h2, self.h3, self.h4
        # extend word list
        w = list(chunk)
        for i in range(16, 80):
            new_word = w[i-3] ^ w[i-8] ^ w[i-14] ^ w[i-16]
            # Leftshift 32 bit
            new_word = self.left_rotate(new_word, 1)
            w.append(new_word)
        # main loop
        for i in range(80):
            if i < 20:
                f = (b & c) | ((~b) & d)
                k = 0x5A827999
            elif i < 40:
                f = b ^ c ^ d
                k = 0x6ED9EBA1
            elif i < 60:
                f = (b & c) | (b & d) | (c & d)
                k = 0x8F1BBCDC
            else:
                f = b ^ c ^ d
                k = 0xCA62C1D6

            temp = (self.left_rotate(a, 5) + f + e + k + w[i]) % 2**32
            e = d
            d = c
            c = self.left_rotate(b, 30)
            b = a
            a = temp

        # update hash digest with chunk data
        self.h0 += a
        self.h1 += b
        self.h2 += c
        self.h3 += d
        self.h4 += e
        self.h0 %= 2**32
        self.h1 %= 2**32
        self.h2 %= 2**32
        self.h3 %= 2**32
        self.h4 %= 2**32

    def digest(self):
        return struct.pack(">IIIII", self.h0, self.h1, self.h2, self.h3, self.h4)

    def hexdigest(self):
        return self.digest().hex()

    def payload(self):
        return self.message, self.hexdigest()
