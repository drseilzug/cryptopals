import aes
import base64


def main():
    b64 = 'L77na/nrFsKvynd6HzOoG7GHTLXsTVu9qvY/2syLXzhPweyyMTJULu/6/kXX0KSvoOLSFQ=='
    ciphertext = base64.b64decode(b64)
    plain = aes.ctr_transform(ciphertext, 'YELLOW SUBMARINE', 0)
    print(plain)


if __name__ == '__main__':
    main()
