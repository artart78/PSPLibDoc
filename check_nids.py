#! /usr/bin/env python3

import psp_libdoc
import glob
import hashlib
from obfuscated_list import obfuscated_list

filelist = glob.glob('PSP*/**/*.xml', recursive=True)
for (idx, file) in enumerate(filelist):
    #if (idx % 100 == 99):
    #    print("%d/%d..." % (idx + 1, len(filelist)))
    entries = psp_libdoc.loadPSPLibdoc(file)
    version = file.split('/')[1]
    for e in entries:
        if e.libraryName in obfuscated_list and float(version) >= float(obfuscated_list[e.libraryName]):
            #print('skip', e.libraryName, version)
            continue
        if not e.name.endswith(e.nid):
            realhash = hashlib.sha1(e.name.encode('ascii')).digest()[:4][::-1].hex().upper()
            if not realhash == e.nid:
                print(realhash, e.nid, e)

