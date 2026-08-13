#!/usr/bin/env python3
"""Patch the 2016 RCCService trust check so content requests are not gated.

The 2016 RCC engine refuses to fetch any content ("Trust check failed") unless
it can validate signed security data from the website. Since we self-host the
site, we patch the check out: at the httpGet trust-check site, `test al,al /
jne` becomes an unconditional jump. Only one xref exists per build.

Usage: python3 tools/patch-trust.py <RCCService.exe> [out.exe]
"""
import sys
import pefile


def find_string_va(pe: pefile.PE, needle: bytes):
    base = pe.OPTIONAL_HEADER.ImageBase
    for sec in pe.sections:
        d = sec.get_data()
        off = d.find(needle)
        if off >= 0:
            return base + sec.VirtualAddress + off
    return None


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else src + ".trustpatched.exe"
    pe = pefile.PE(src, fast_load=False)
    image_base = pe.OPTIONAL_HEADER.ImageBase

    va_str = find_string_va(pe, b"Trust check failed")
    if not va_str:
        print("string not found (already patched?)")
        return 1
    print("string at 0x%x" % va_str)

    code = [s for s in pe.sections if s.Name.rstrip(b"\x00") == b".text"][0]
    data = bytearray(open(src, "rb").read())
    text_data = code.get_data()
    base = image_base + code.VirtualAddress
    pat = struct_pack_u32(va_str)
    pos = 0
    xrefs = []
    while True:
        pos = text_data.find(pat, pos)
        if pos < 0:
            break
        xrefs.append(base + pos)
        pos += 1
    print("xrefs:", [hex(h) for h in xrefs])

    patched = 0
    for xref in xrefs:
        # the check site is the pattern: test al,al; jne +disp  (~10 bytes
        # after the push of the string). scan a small window after the xref.
        rva = xref - base
        window = text_data[rva : rva + 40]
        idx = window.find(b"\x84\xc0")
        while idx >= 0:
            va = base + rva + idx
            # verify a conditional jump follows within 6 bytes
            jb = window[idx + 2 : idx + 8]
            if jb and (jb[0] & 0xF0) == 0x70:  # jcc short
                # compute landing: jmp from `va` with disp+0x14 needs jcc
                # disp+0x12 from va+2. We overwrite test (2 bytes) with EB disp.
                disp = jb[1] + 0x14 - 2  # rel8 from va+2 to same target
                if -128 <= disp <= 127:
                    fo = code.PointerToRawData + rva + idx
                    data[fo : fo + 2] = bytes([0xEB, disp & 0xFF])
                    print("patched 0x%x: jmp short over trust failure" % va)
                    patched += 1
                    break
            idx = window.find(b"\x84\xc0", idx + 1)
    if patched == 0:
        print("could not locate a patchable check site")
        return 1
    open(out, "wb").write(data)
    print("wrote %s (%d sites patched)" % (out, patched))
    return 0


def struct_pack_u32(v):
    import struct
    return struct.pack("<I", v)


if __name__ == "__main__":
    sys.exit(main())
