from Crypto.Util.number import getStrongPrime
import secrets
from mpmath import mp, mpf

p = getStrongPrime(1024)
q = getStrongPrime(1024)
n = p*q
e = 65537

phi = (p-1)*(q-1)
d = pow(e, -1, phi)

mp.dps = 8192
leak = mpf(secrets.randbelow(n)) / mpf(phi) + mpf(secrets.randbelow(n)) / mpf(n)
leak *= 2**8192

flag = open('flag.txt').read().strip()
assert len(flag) == 32
flag = int.from_bytes(flag.encode(), 'big')
ct = pow(flag, e, n)

print(f"n = {n}")
print(f"ct = {ct}")
print(f"leak = {int(leak)}")
