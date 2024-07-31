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

def ELTMiMC_hash(inp: bytes, apply_padding=True):
    if apply_padding:
        inp = pad(inp, 32)
    blocks = [inp[i:i+32] for i in range(0, len(inp), 32)]
    blocks_F = [F.from_integer(bytes_to_long(b)) for b in blocks]

    state = iv
    for block in blocks_F:
        state += ELTMiMC(g(state), block)
        # print('->', long_to_bytes(state.to_integer()).hex())
    return long_to_bytes(state.to_integer())



############################################

from sage.all import Matrix, vector, random_vector, random_matrix, ZZ, copy

# x -> x^2
square_matrix = Matrix(GF(2), ncols=256, nrows=256)
for i in range(256):
    x = 1 << i
    x = F.from_integer(x)
    y = x ** 2
    y = y.to_integer()
    for j in range(256):
        square_matrix[j, i] = (y >> j) & 1

x = F.random_element()
x_vector = vector(GF(2), [int(x.to_integer() >> i) & 1 for i in range(256)])

y_vector = square_matrix * x_vector
y = x*x
y = y.to_integer()
assert y == sum([int(y_vector[i]) << i for i in range(256)])

def int_to_vector(x):
    return vector(GF(2), [int(x >> i) & 1 for i in range(256)])

def vector_to_int(v):
    return sum([int(v[i]) << i for i in range(256)])


def recover_pt_given_target(key, target):
    """
    x + c1
    M(x + c1) = Mx + Mc1
    M(Mx + Mc1 + c2) = MMx + MMc1 + Mc2
    ...

    M^64 x + M^64 c1 + M^63 c2 + ... + Mc64 + key
    """
    tot_rounds = 63
    mimc_matrix = copy(square_matrix)**tot_rounds

    mimc_const_term = vector(GF(2), [0]*256)
    for i, c in enumerate(constants[:tot_rounds]):
        constant_vector = int_to_vector(c.to_integer()) + int_to_vector(key.to_integer())
        # print(i, tot_rounds-i)
        constant_vector = (square_matrix**(tot_rounds - i)) * constant_vector
        mimc_const_term += constant_vector
    # mimc_const_term += int_to_vector(key.to_integer())

    # print(mimc_matrix)
    # print(mimc_const_term)
    target_vector = int_to_vector(target.to_integer())

    x = mimc_matrix.solve_right(target_vector - mimc_const_term)
    x = vector_to_int(x)
    return x

key = F.random_element()
target = F.random_element()
print("Target:", target.to_integer())
x = recover_pt_given_target(key, target)
print((ELTMiMC(F.from_integer(x), key)).to_integer())

def recover_key_given_target(pt, target):
    """
    x + c1 + pt
    M(x + c1 + pt) = Mx + Mc1 + Mpt

    M(Mx + Mc1 + c2 + x) = MMx + MMc1 + Mc2 + Mx = (MM + M)x + MMc1 + Mc2 + Mpt
    ...

    M^64 x + M^64 c1 + M^63 c2 + ... + Mc64 + key
    """
    tot_rounds = 63
    mimc_matrix = copy(square_matrix)**tot_rounds
    for i in range(1, tot_rounds):
        mimc_matrix += copy(square_matrix)**(tot_rounds - i)

    mimc_const_term = vector(GF(2), [0]*256)
    for i, c in enumerate(constants[:tot_rounds]):
        constant_vector = int_to_vector(c.to_integer())
        # print(i, tot_rounds-i)
        constant_vector = (square_matrix**(tot_rounds - i)) * constant_vector
        mimc_const_term += constant_vector
    mimc_const_term += copy(square_matrix)**tot_rounds * int_to_vector(pt.to_integer())

    # print(mimc_matrix)
    # print(mimc_const_term)
    target_vector = int_to_vector(target.to_integer())

    x = mimc_matrix.solve_right(target_vector - mimc_const_term)
    x = vector_to_int(x)
    return x

pt = F.random_element()
target = F.random_element()
print("Target:", target.to_integer())
x = recover_key_given_target(pt, target)
print((ELTMiMC(pt, F.from_integer(x))).to_integer())

import os
while True:
    # generate_collision
    m1 = b"ELTMiMC: ".ljust(32, b'A') + os.urandom(32)

    m2_base = pad(m1, 32)

    h1 = ELTMiMC_hash(m1)
    h2 = ELTMiMC_hash(m2_base, apply_padding=False)
    print(h1.hex())

    h1f = F.from_integer(bytes_to_long(h1))
    h2f = F.from_integer(bytes_to_long(h2))
    block = recover_key_given_target(g(h2f), h1f - h2f)
    print('block:', long_to_bytes(block).hex())
    if long_to_bytes(block)[-1] == 1:
        break


h_forged = ELTMiMC_hash(m2_base + long_to_bytes(block), apply_padding=False)
print(h_forged.hex())

print(m1.hex())
print((m2_base + long_to_bytes(block)[:-1]).hex())

"""
454c544d694d433a204141414141414141414141414141414141414141414141c41391e17c2b6c862b7fb1405f273fef4753ea6c5a1890a4c1486a21d5a3d62d
454c544d694d433a204141414141414141414141414141414141414141414141c41391e17c2b6c862b7fb1405f273fef4753ea6c5a1890a4c1486a21d5a3d62d20202020202020202020202020202020202020202020202020202020202020209b2607ded8de162ab1f03490806f9b1890cad7444f8b9e88770e42e24a79be
"""