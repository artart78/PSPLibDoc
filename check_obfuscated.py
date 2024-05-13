#! /usr/bin/env python3

import psp_libdoc
import glob
from collections import defaultdict

def print_status(module, lib, version, obfuscated, cur_nids, prev_nonobf, prev_ok):
    #print("---", lib, version, obfuscated)
    unk_nids = []
    nok_nids = []
    ok_nids = []
    for (nid, name) in cur_nids:
        if not obfuscated:
            prev_nonobf[nid] = (version, name)
        if name.endswith(nid):
            unk_nids.append((nid, name))
        elif psp_libdoc.compute_nid(name) == nid:
            ok_nids.append((nid, name))
        else:
            nok_nids.append((nid, name))
    #print("out of %d %snids:" % (len(cur_nids), "obfuscated " if obfuscated else ""))
    if obfuscated:
        nok_dubious = []
        nok_from_prev = []
        for (nid, name) in nok_nids:
            if nid in prev_ok or nid in prev_nonobf:
                print("WARN: previously seen non-obfuscated:", module, lib, version, nid, name, prev_nonobf[nid])
            found_prev = False
            for nid2 in prev_ok:
                if prev_ok[nid2][1] == name:
                    found_prev = True
                    break
            if not found_prev:
                #print("WARN: name coming from unknown source:", (nid, name))
                nok_dubious.append((nid, name))
            else:
                nok_from_prev.append((nid, name))

        unk_nonobf = []
        unk_obf = []
        for (nid, name) in unk_nids:
            if nid in prev_ok: # could by prev_nonobf, for pure information
                print("WARN: previously seen non-obfuscated OK:", module, lib, version, nid, prev_ok[nid])
            if nid in prev_nonobf:
                unk_nonobf.append((nid, name))
            else:
                unk_obf.append((nid, name))
        stats = {"known": ok_nids, "unknown_nonobf": unk_nonobf, "unknown_obf": unk_obf, "nok_from_previous": nok_from_prev, "nok_dubious": nok_dubious}
    else:
        for (nid, name) in (nok_nids + unk_nids):
            if nid in prev_ok:
                print("WARN: previously seen OK:", module, lib, version, nid, name, prev_ok[nid])
        if len(nok_nids) > 0:
            print("WARN: wrong NIDs:", module, lib, version, nok_nids)
        stats = {"known": ok_nids, "unknown": unk_nids, "wrong": nok_nids}

    print(module, lib, version, {cat: "%.0f%%" % (len(stats[cat]) / len(cur_nids) * 100) for cat in stats})

    for (nid, name) in ok_nids:
        prev_ok[nid] = (version, name)

def main():
    nid_bylib = defaultdict(lambda: defaultdict(set))
    lib_info = {}

    filelist = glob.glob('ePSP*/*/Export/**/*.xml', recursive=True)
    for (idx, file) in enumerate(filelist):
        version = file.split('/')[1]
        entries = psp_libdoc.loadPSPLibdoc(file)
        for e in entries:
            lib_info[e.libraryName] = (file.split('/')[-1].replace('xml', 'prx'), e.libraryFlags)
            nid_bylib[e.libraryName][version].add((e.nid, e.name))

    for (lib, libinfo) in sorted(lib_info.items(), key = lambda x: (x[1][0], x[0])):
        #print("=============", libinfo[0], lib, "===============")
        vers = list(sorted(nid_bylib[lib].keys()))
        now_obfuscated = False
        prev_nonobf = {}
        prev_ok = {}
        print_status(libinfo[0], lib, vers[0], now_obfuscated, nid_bylib[lib][vers[0]], prev_nonobf, prev_ok)
        for (v1, v2) in zip(vers, vers[1:]):
            v1_nids = set([x[0] for x in nid_bylib[lib][v1]])
            v2_nids = set([x[0] for x in nid_bylib[lib][v2]])
            new_nids = v2_nids - v1_nids
            disappear_nids = v1_nids - v2_nids
            new_ratio = len(new_nids) / len(v2_nids)
            dis_ratio = len(disappear_nids) / len(v1_nids)
            is_obfuscated = False
            if new_ratio > 0.2 and dis_ratio > 0.2:
                is_obfuscated = True
                for n in new_nids:
                    name = None
                    for (x, y) in nid_bylib[lib][v2]:
                        if x == n:
                            name = y
                    if compute_nid(name) == n and v1 != '5.55': # some exceptions exist for 5.55 (which misses functions from 5.51)
                        #print('ERROR:', n, name)
                        is_obfuscated = False
            if is_obfuscated:
                kept = len(v1_nids & v2_nids)
                #print(f"{lib} {v1} -> {v2}     obfuscated, {new_ratio*100:.0f}% new, {dis_ratio*100:.0f}% disappeared out of {len(v1_nids)}, yet {kept} NIDs remain")
                now_obfuscated = True
            else:
                pass
                #print(f"{lib} {v1} -> {v2} NOT obfuscated, {new_ratio*100:.0f}% new, {dis_ratio*100:.0f}% disappeared out of {len(v1_nids)}")
            print_status(libinfo[0], lib, v2, now_obfuscated, nid_bylib[lib][v2], prev_nonobf, prev_ok)

if __name__ == '__main__':
    main()

