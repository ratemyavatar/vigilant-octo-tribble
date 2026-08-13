#!/usr/bin/env python3
"""Tiny pkg-config stand-in used to build libglvnd in sandboxes without it.

Looks for .pc files in $PKG_CONFIG_PATH (or alongside this script) and prints
the usual cflags/libs/version output. Only supports the subset meson needs.
"""
import os
import re
import sys


def load(name, pc_dir):
    for d in pc_dir.split(":") + [os.path.dirname(os.path.abspath(__file__))]:
        p = os.path.join(d, name + ".pc")
        if os.path.isfile(p):
            vars_ = {}
            for m in re.finditer(r"^([A-Za-z0-9_]+)\s*[=:]\s*(.+)$", open(p).read(), re.M):
                vars_[m.group(1)] = m.group(2)
            return vars_
    return None


def expand(v, vars_):
    for _ in range(5):
        for k, val in list(vars_.items()):
            v = v.replace("${%s}" % k, val)
    return v


def main():
    args = sys.argv[1:]
    pc_dir = os.environ.get("PKG_CONFIG_PATH", "/tmp")
    modes, pkgs = [], []
    for a in args:
        if a.startswith("--"):
            modes.append(a[2:])
        else:
            pkgs.append(a)

    if "atleast-pkgconfig-version" in modes:
        return 0
    if "version" in modes and not pkgs:
        print("1.8.1")
        return 0

    for name in pkgs:
        p = load(name, pc_dir)
        if p is None:
            sys.stderr.write("Package '%s' not found\n" % name)
            return 1
        p.setdefault("Version", "0")
        p.setdefault("prefix", "/usr")
        for k in list(p.keys()):
            p[k] = expand(p[k], p)

    if "modversion" in modes or "version" in modes:
        print(p["Version"])
    if "cflags" in modes:
        print(p.get("Cflags", ""))
    if "libs" in modes:
        print(p.get("Libs", ""))
    if "exists" in modes:
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
