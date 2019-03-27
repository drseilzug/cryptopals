import aes
import base64


def main():
    ciphertext = b""
    key = "YELLOW SUBMARINE"
    with open('25.txt', 'r') as f:
        ciphertext = base64.b64decode(f.read())
    plain = aes.decrypt_ecb_aes(ciphertext, key)
    print(plain)


if __name__ == '__main__':
    main()
