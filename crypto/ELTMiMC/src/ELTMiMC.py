from sage.all import GF
from Crypto.Util.number import long_to_bytes, bytes_to_long
from Crypto.Util.Padding import pad
from hashlib import sha256

F = GF(2**256, 'x')
x = F.gen()

nothing_up_my_sleeve = b"ELTMiMC: Even Less Than Minimal Multiplicative Complexity"
constants = [F.from_integer(bytes_to_long(sha256(nothing_up_my_sleeve + b' constant ' + long_to_bytes(i)).digest())) for i in range(63)]
coeffs = [F.from_integer(bytes_to_long(sha256(nothing_up_my_sleeve + b' coeff ' + long_to_bytes(i)).digest())) for i in range(8)]
iv = F.from_integer(bytes_to_long(sha256(nothing_up_my_sleeve + b' iv').digest()))

def ELTMiMC(pt, key):
    for const in constants:
        pt = pt + const + key
        pt = pt**2
    return pt

def g(x):
    res = 0
    for coeff in coeffs:
        res = res * x + coeff
    return res

def ELTMiMC_hash(inp: bytes):
    inp = pad(inp, 32)
    blocks = [inp[i:i+32] for i in range(0, len(inp), 32)]
    blocks_F = [F.from_integer(bytes_to_long(b)) for b in blocks]

    state = iv
    for block in blocks_F:
        state += ELTMiMC(g(state), block)
    return long_to_bytes(state.to_integer())


print("Welcome to the ELTMiMC collision challenge!")
m1 = bytes.fromhex(input("Enter the first message (hex): "))
m2 = bytes.fromhex(input("Enter the second message (hex): "))
assert len(m1) >= 64 and len(m2) >= 64
assert m1 != m2
assert m1.startswith(b"ELTMiMC: ") and m2.startswith(b"ELTMiMC: ")

if ELTMiMC_hash(m1) == ELTMiMC_hash(m2):
    with open("flag.txt") as f:
        print(f"Congratulations! Here is your flag: {f.read()}")
else:
    print("Nope :/")
