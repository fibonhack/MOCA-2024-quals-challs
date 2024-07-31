# docker run --rm -it -v $(pwd):/here -w /here --network host lor3nz/sage -python solve.py 'http://localhost:5000'
import sys
from sage.all import *
import json
from base64 import b64decode, b64encode
import requests

# see here for crc: https://stackoverflow.com/questions/2587766/how-is-a-crc32-checksum-calculated


PR = PolynomialRing(GF(2), 'x')
x = PR.gen()

mod = x**32 + x**26 + x**23 + x**22 + x**16 + x**12 + x**11 + x**10 + x**8 + x**7 + x**5 + x**4 + x**2 + x + 1

def i2p(n: int) -> Polynomial:
	"""int to polynomial"""
	return PR([(n>>i)&1 for i in range(int(n).bit_length())])

def p2i(p: Polynomial) -> int:
	"""polynomial to int"""
	return int("".join(str(b) for b in (p.list() or (0,))[::-1]), 2)

def revbitsbyte(x: bytes) -> bytes:
	return bytes(int(f"{b:08b}"[::-1], 2) for b in x)

def xor(a: bytes, b: bytes, *, strict=True) -> bytes:
	if strict and len(a) != len(b):
		raise ValueError("xor length mismatch")
	return bytes(x^y for x, y in zip(a, b))


def delta_crc_from_delta_data(dx: bytes) -> bytes:
	"""given unknown `data` and a known delta `dx` that
	calculates delta_crc s.t. `crc(data ^ dx) = crc(data) ^ delta_crc`

	easy enough since crc is kind of linear"""


	d_r = revbitsbyte(dx) # invert bits in every byte
	d_i = int.from_bytes(d_r, 'big')
	d_p = i2p(d_i) * x**32 
	d_crc = p2i(d_p % mod)
	delta_crc = int(f"{d_crc:032b}"[::-1], 2)  # invert all bits
	return delta_crc.to_bytes(4, 'little')

# innermost layer
original = b"{'won': 0, 'tied': 0, 'lost': 0, 'played': 0, 'id': 'xxxxxxxxxxxxxxxxxxxxxx=='}"
target   = b"{'won':100,'tied': 0, 'lost': 0, 'played':99, 'id': 'xxxxxxxxxxxxxxxxxxxxxx=='}"
dx = xor(original, target)
delta_crc = delta_crc_from_delta_data(dx)


# outer layer
original = bytes(8) + original + bytes(4)
target = bytes(8) + target + delta_crc

dx2 = xor(original, target)
delta_crc2 = delta_crc_from_delta_data(dx2)

delta_token = bytes(8) + dx2 + delta_crc2

# get token
URL = sys.argv[1]
token = b64decode(requests.get(URL).cookies['session'])
print(f"original token: {token.hex()}")

win_token = xor(token, delta_token)

print(f"forged token: {win_token.hex()}")

while True:
	r = requests.post(f"{URL}/play/rock", cookies={'session':b64encode(win_token).decode()}).json()
	print(r)
	if 'flag' in r:
		break