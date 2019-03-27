"""
Methods to encode and decode data inbetween various formats.

The following types are returned as regular utf-8 python strings unless the
out_as_bytes flag is set:
hex
base64

These types are returned as bytestrings unless out_as_bytes is set to False:
bytes
"""
import base64
import codecs


def hex_to_b64(hexstring, out_as_bytes=False):
    """ returns a base64 encoded byte string from a hex encoded string """
    try:
        hexstring = hexstring.decode()
    except AttributeError:
        pass
    b64_bytestring = base64.b64encode(bytes.fromhex(hexstring))
    if out_as_bytes:
        return b64_bytestring
    else:
        return b64_bytestring.decode()


def b64_to_hex(b64string, out_as_bytes=False):
    """Returns hex string from b64string"""
    hex_bytestring = codecs.encode(base64.b64decode(b64string), 'hex')
    if out_as_bytes:
        return hex_bytestring
    else:
        return hex_bytestring.decode()


def hex_to_bytes(hexstring, out_as_bytes=True):
    """ converts hex data to bytes. Returns bytestrings by default"""
    outstring = bytes.fromhex(hexstring)
    if not out_as_bytes:
        return outstring.decode()
    else:
        return outstring


def bytes_to_hex(bytesstring, out_as_bytes=False):
    """encodes bytes data to hex. Returns strings by default"""
    try:
        bytesstring = bytesstring.encode()
    except AttributeError:
        pass
    out_bytes = bytesstring.hex()
    if out_as_bytes:
        return out_bytes
    else:
        return out_bytes.decode()


# Testing Environment
if __name__ == '__main__':
    b64 = 'SSdtIGtpbGxpbmcgeW91ciBicmFpbiBsaWtlIGEgcG9pc29ub3VzIG11c2hyb29t'
    b64_b = b'SSdtIGtpbGxpbmcgeW91ciBicmFpbiBsaWtlIGEgcG9pc29ub3VzIG11c2hyb29t'
    hex_to_b64(b64_to_hex(b64))
    hex_to_b64(b64_to_hex(b64_b, True))
