#!/usr/bin/python3

from collections import defaultdict
import Levenshtein
import re
import subprocess
import sys

def run_prxtool(binary_path):
    return subprocess.check_output(["prxtool", "-w", binary_path]).decode('ascii')

def get_raw_functions(binary_path):
    data = run_prxtool(binary_path)
    funs = defaultdict(str)
    cur_fun = None
    names = []
    for line in data.split('\n'):
        if 'Subroutine' in line:
            # ; Subroutine sceUsb_C21645A4 - Address 0x00002F40 - Aliases: sceUsb_driver_C21645A4, sceUsbBus_driver_C21645A4
            m = re.match(r"; Subroutine ([^ ]*) .*", line)
            names = [m.groups()[0]]
            alias_pos = line.find("Aliases: ")
            if alias_pos != -1:
                alias_str = line[alias_pos + len("Aliases: "):]
                names += alias_str.split(", ")
        elif line.startswith('\t0x'):
            m = re.match(r"\t0x[0-9A-F]{8}: 0x([0-9A-F]{8})", line)
            data = m.groups()[0]
            for n in names:
                funs[n] += data
        elif '; Imported from' in line:
            break
    return funs

def match_module_pair(path1, path2):
    funs1 = get_raw_functions(path1)
    funs2 = get_raw_functions(path2)
    libcounts1 = defaultdict(int)
    libcounts2 = defaultdict(int)
    #distances = defaultdict(dict)
    first = True
    for (f1, c1) in funs1.items():
        if f1.startswith('sub_'):
            continue
        lib1 = f1[:-8]
        min_dist = None
        best_match = None
        libcounts1[lib1] += 1
        for (f2, c2) in funs2.items():
            if f2.startswith('sub_'):
                continue
            lib2 = f2[:-8]
            if lib1 != lib2:
                continue
            if first:
                libcounts2[lib2] += 1
            cur_dist = Levenshtein.distance(c1, c2)
            if min_dist is None or cur_dist < min_dist:
                min_dist = cur_dist
                best_match = f2
        first = False
        print(f1, best_match, min_dist)

if __name__ == '__main__':
    #get_raw_functions(sys.argv[1])
    match_module_pair(sys.argv[1], sys.argv[2])


