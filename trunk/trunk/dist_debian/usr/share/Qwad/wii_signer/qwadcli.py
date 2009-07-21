#!/usr/bin/env python
#-*- coding: utf-8 -*-
from wiiw import *

def update(directory):
    os.chdir(directory)
    tmd = TMD(open('tmd', 'rb').read())
    for content in tmd.contents:
        app = open("%08x.app" % content.index, 'rb').read()
        content.size = len(app)
        content.hash = hashlib.sha1(app).digest()
    tmd.fakesign()
    tmd.fixpayload()
    if outputoverride:
        open(output, 'wb').write(tmd.pack())
    else:
        open('tmd', 'wb').write(tmd.pack())

def extract(filename):
    wad = WAD(filename)
    if outputoverride:
        try:
            os.mkdir(output)
        except OSError:
            pass
        os.chdir(output)
    else:
        try:
            os.mkdir("%016x" % wad.ticket.titid)
        except OSError:
            pass
        os.chdir("%016x" % wad.ticket.titid)
    open('ticket', 'wb').write(wad.rawtik)
    open('tmd', 'wb').write(wad.rawtmd)
    open('cert', 'wb').write(wad.rawcert)
    open('wad_timestamp', 'wb').write(wad.timestamp)
    for i in range(0, len(wad.apps)):
        open("%08x.app" % wad.tmd.contents[i].index, 'wb').write(wad.apps[i].decrypted[:wad.tmd.contents[i].size])
    os.chdir('..')

def packdir(directory):
    os.chdir(directory)
    footersize = 0
    try:
        timestamp = open('wad_timestamp', 'rb').read()
        footersize = len(timestamp)
    except IOError:
        print "No timestamp found, name it 'wad_timestamp' if you want to include one.\n"
    rawtik = open('ticket', 'rb').read()
    ticket = Ticket(rawtik)
    rawtmd = open('tmd', 'rb').read()
    tmd = TMD(rawtmd)
    rawcert = open('cert', 'rb').read()
    cert = rawcert
    pack = struct.pack('>I4s6I', 32, "Is\x00\x00", len(cert), 0, 676, 484 + (36 * tmd.contnum), tmd.datasize(), footersize) + "\x00" * 32
    pack += rawcert
    if len(rawcert) % 64 != 0:
        pack += "\x00" * (64 - (len(rawcert) % 64))
    pack += (rawtik + "\x00" * 28)
    pack += rawtmd
    if len(rawtmd) % 64 != 0:
        pack += "\x00" * (64 - (len(rawtmd) % 64))
    apps = []
    for content in tmd.contents:
        apps.append(APP(open("%08x.app" % content.index, 'rb').read(), ticket.titlekey, struct.pack('>H', content.index) + "\x00" * 14, False))
        apps[-1].encrypt()
        pack += apps[-1].encrypted
        if len(apps[-1].encrypted) % 64 != 0:
            pack += "\x00" * (64 - (len(apps[-1].encrypted) % 64))
    if footersize > 0:
        pack += timestamp
        pack += "\x00" * (64 - (len(timestamp) % 64))
    os.chdir('..')
    if outputoverride:
        open(output, 'wb').write(pack)
    else:
        open("%016x.wad" % ticket.titid, 'wb').write(pack)

if __name__ == '__main__':
    import getopt, sys
    usage = "Usage: python wii.py [options]\n\n\t-o dir, --output=outputdir: Specify output directory for wad extraction (default is titleid), or output file for packing.\n\t-f file.wad, --file=file.wad: File to extract (WAD)\n\t-d inputdir, --directory=inputdir: Specify a directory of files to make a wad from\n\t-u updatedir, --update=updatedir: Update the TMD in the specified folder for correct sizes and hashes, then fakesign it.\n\n"
    if len(sys.argv) == 1:
        sys.stderr.write(usage)
        sys.exit(1)
    outputoverride = False
    try:
        optlist, args = getopt.gnu_getopt(sys.argv[1:], 'd:f:o:u:', ['directory=', 'file=', 'output=', 'update='])
    except getopt.GetoptError, err:
        sys.stderr.write(str(err) + "\n\n" + usage)
        sys.exit(1)
    for o, v in optlist:
        if o in ('-o', '--output'):
            outputoverride = True
            global output
            output = v
        if o in ('-u', '--update'):
            update(v)
            sys.exit(0)
        if o in ('-f', '--file'):
            extract(v)
            sys.exit(0)
        if o in ('-d', '--directory'):
            packdir(v)
            sys.exit(0)

