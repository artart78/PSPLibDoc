#! /usr/bin/env python3

import psp_libdoc
import glob
import sys
from collections import defaultdict

OUTPUT_HTML = "./"
HTML_STATUS = [
    # for both obfuscated and non-obfuscated
    ("known", "green", "matching the name hash"),
    # for non-obfuscated
    ("unknown", "orange", "unknown"),
    ("wrong", "red", "not matching the name hash"),
    # for obfuscated
    ("nok_from_previous", "yellow", "obfuscated but matching a previous non-obfuscated name"),
    ("nok_dubious", "brown", "obfuscated but found from an unknown source"),
    ("unknown_nonobf", "orange", "unknown and non-obfuscated"),
    ("unknown_obf", "grey", "unknown but obfuscated")
]

def html_header(versions):
    header = """<!DOCTYPE html>
<html>
<title>PSP NID Status</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="https://www.w3schools.com/w3css/4/w3.css">
<style>
.w3-container, .w3-panel {
    padding: 0em 0px;
}
.w3-col {
    height:24px;
}
</style>
<body>
<div class="w3-container" style="height:100vh; width:100vw; overflow: scroll;">"""
    header += """<table class="w3-table"><tr><th>Module name</th><th>Library name</th>"""
    for ver in versions:
        header += f"<th>{ver}</th>"
    header += "</tr>"
    return header

def html_footer():
    return """</table></div></body></html>"""

def html_module(module, lib, stats_byver, versions):
    output = f"<tr><td>{module}</td><td>{lib}</td>"
    for ver in versions:
        if ver not in stats_byver:
            output += "<td></td>"
            continue
        output += "<td>"
        cur_stats = stats_byver[ver][0]
        is_obf = stats_byver[ver][1]
        if is_obf:
            obf_str = '<div style="position: absolute; width: 100%; height: 100%; text-align: center;">*</div>'
        else:
            obf_str = ''

        for (status, color, desc) in HTML_STATUS:
            if status not in cur_stats:
                continue
            count = len(cur_stats[status])
            if count == 0:
                continue
            total = cur_stats['total']
            percent = int(count / total * 100)

            output += f"""<div style="position: relative;"><div class="w3-col w3-container w3-{color} w3-tooltip" style="width:{percent}%">
<span style="position:absolute;left:0;bottom:18px" class="w3-text w3-tag">{count}/{total} NIDs are {desc}</span>
</div>"""
        output += f"{obf_str}</div></td>"
    return output

def make_stats(module, lib, version, obfuscated, cur_nids, prev_nonobf, prev_ok, stats_bynid):
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
    if obfuscated:
        nok_dubious = []
        nok_from_prev = []
        for (nid, name) in nok_nids:
            if nid in prev_ok or nid in prev_nonobf:
                print("WARN: previously seen non-obfuscated:", module, lib, version, nid, name, prev_nonobf[nid], file=sys.stderr)
            found_prev = False
            for nid2 in prev_ok:
                if prev_ok[nid2][1] == name:
                    found_prev = True
                    break
            if not found_prev:
                nok_dubious.append((nid, name))
            else:
                nok_from_prev.append((nid, name))

        unk_nonobf = []
        unk_obf = []
        for (nid, name) in unk_nids:
            if nid in prev_ok: # could by prev_nonobf, for pure information
                print("WARN: previously seen non-obfuscated OK:", module, lib, version, nid, prev_ok[nid], file=sys.stderr)
            if nid in prev_nonobf:
                unk_nonobf.append((nid, name))
            else:
                unk_obf.append((nid, name))
        stats = {"known": ok_nids, "unknown_nonobf": unk_nonobf, "unknown_obf": unk_obf, "nok_from_previous": nok_from_prev, "nok_dubious": nok_dubious}
    else:
        for (nid, name) in (nok_nids + unk_nids):
            if nid in prev_ok:
                print("WARN: previously seen OK:", module, lib, version, nid, name, prev_ok[nid], file=sys.stderr)
        if len(nok_nids) > 0:
            print("WARN: wrong NIDs:", module, lib, version, nok_nids, file=sys.stderr)
        stats = {"known": ok_nids, "unknown": unk_nids, "wrong": nok_nids}

    #print(module, lib, version, {cat: "%.0f%%" % (len(stats[cat]) / len(cur_nids) * 100) for cat in stats})
    stats['total'] = len(cur_nids)

    for (nid, name) in ok_nids:
        prev_ok[nid] = (version, name)

    return stats

def main():
    nid_bylib = defaultdict(lambda: defaultdict(set))
    lib_info = {}

    filelist = glob.glob('PSP*/*/Export/**/*.xml', recursive=True)
    versions = set()
    for (idx, file) in enumerate(filelist):
        version = file.split('/')[1]
        versions.add(version)
        entries = psp_libdoc.loadPSPLibdoc(file)
        for e in entries:
            lib_info[e.libraryName] = (file.split('/')[-1].replace('xml', 'prx'), e.libraryFlags)
            nid_bylib[e.libraryName][version].add((e.nid, e.name))

    versions = list(sorted(versions))
    html_output = html_header(versions)
    for (lib, libinfo) in sorted(lib_info.items(), key = lambda x: (x[1][0], x[0])):
        vers = list(sorted(nid_bylib[lib].keys()))
        now_obfuscated = False
        prev_nonobf = {}
        prev_ok = {}
        stats_byver = {vers[0]: (make_stats(libinfo[0], lib, vers[0], now_obfuscated, nid_bylib[lib][vers[0]], prev_nonobf, prev_ok), False)}
        stats_bynid = {}
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
                    if psp_libdoc.compute_nid(name) == n and v1 != '5.55': # some exceptions exist for 5.55 (which misses functions from 5.51)
                        is_obfuscated = False
            if is_obfuscated:
                kept = len(v1_nids & v2_nids)
                now_obfuscated = True
            stats_byver[v2] = (make_stats(libinfo[0], lib, v2, now_obfuscated, nid_bylib[lib][v2], prev_nonobf, prev_ok, stats_bynid), is_obfuscated)
        html_output += html_module(libinfo[0], lib, stats_byver, versions)
    html_output += html_footer()
    with open(OUTPUT_HTML + '/' + index.html, 'w') as fd:
        fd.write(html_output)

if __name__ == '__main__':
    main()

