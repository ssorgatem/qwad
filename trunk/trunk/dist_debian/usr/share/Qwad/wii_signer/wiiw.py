#-*- coding: utf-8 -*-
"""
Module reimplementing Wii Signer's functions
"""
import os
import struct
import hashlib
import string
from PyQt4.QtCore import QString
from PyQt4.QtGui import QMessageBox
from Crypto.Cipher import AES

class Ticket:
    def __init__(self, string):
        self.rsaexp, self.rsamod, self.misc1, self.rsaid, self.misc2, self.key, self.misc3, self.tikid, self.dev, self.titid, self.mask, self.reserved, self.cidxmask, self.padding, self.limits = struct.unpack('>I256s60s64s63s16sBQIQH60s64sH64s', string)
        self.CKpath = os.path.expanduser('~') + '/.wii/common-key'
        try:
            self.commonkey = open(self.CKpath, 'rb').read(16)
            CKfound = self.CKpath + " found"
            print CKfound

        except:
            NoCK = QString("%1 not found!").arg(self.CKpath)
            print NoCK
            QMessageBox.critical(None,
                self.trUtf8("Error!"),
                self.trUtf8(NoCK),
                QMessageBox.StandardButtons(\
                    QMessageBox.Abort))

        self.titleiv = struct.pack(">Q", self.titid) + "\x00\x00\x00\x00\x00\x00\x00\x00"
        self.titlekey = AES.new(self.commonkey, AES.MODE_CBC, self.titleiv).decrypt(self.key)

    def fakesign(self):
        self.rsamod = "\x00" * 256

    def pack(self):
        return struct.pack('>I256s60s64s63s16sBQIQH60s64sH64s', self.rsaexp, self.rsamod, self.misc1, self.rsaid, self.misc2, self.key, self.misc3, self.tikid, self.dev, self.titid, self.mask, self.reserved, self.cidxmask, self.padding, self.limits)

    def fixpayload(self):
        for i in range(0, 65536):
            self.padding = i
            if hashlib.sha1(self.pack()).hexdigest()[:2] == '00':
                break
            if i == 65535:
                print "Error, cannot adjust payload correctly."

class TMDContent:
    def __init__(self, string):
        self.cid, self.index, self.type, self.size, self.hash = struct.unpack('>IHHQ20s', string)

    def pack(self):
        return struct.pack('>IHHQ20s', self.cid, self.index, self.type, self.size, self.hash)

class TMD:
    def __init__(self, string):
        self.rsaexp, self.rsamod, self.misc1, self.rsaid, self.version, self.caversion, self.signerversion, self.misc2, self.systemversion, self.titleid, self.titletype, self.groupid, self.reserved, self.accessrights, self.titleversion, self.contnum, self.bootindex, self.padding = struct.unpack('>I256s60s64s4B2QIH62sI4H', string[:484])
        self.contents = []
        for self._i in range(0, self.contnum):
            self.contents.append(TMDContent(string[484+(self._i*36):520+(self._i*36)]))

    def fakesign(self):
        self.rsamod = "\x00" * 256

    def pack(self):
        self._pack = struct.pack('>I256s60s64s4B2QIH62sI4H', self.rsaexp, self.rsamod, self.misc1, self.rsaid, self.version, self.caversion, self.signerversion, self.misc2, self.systemversion, self.titleid, self.titletype, self.groupid, self.reserved, self.accessrights, self.titleversion, self.contnum, self.bootindex, self.padding)
        for self._i in self.contents:
            self._pack += self._i.pack()
        return self._pack

    def fixpayload(self):
        for i in range(0, 65536):
            self.padding = i
            if hashlib.sha1(self.pack()).hexdigest()[:2] == '00':
                break
            if i == 65535:
                print "Error, cannot adjust payload correctly."

    def datasize(self):
        self._d = 0
        for content in self.contents:
            self._d += content.size
            if self._d % 64 != 0:
                self._d += 64 - (content.size % 64)
        return self._d

class APP:
    def __init__(self, data, titlekey, iv, isencrypted=True):
        if isencrypted == True:
            self.encrypted = data
        else:
            self.decrypted = data
        self.key = titlekey
        self.iv = iv
    def decrypt(self):
        if len(self.encrypted) % 16 != 0:
            self.decrypted = AES.new(self.key, AES.MODE_CBC, self.iv).decrypt(self.encrypted + ("\x00" * (16 - (len(self.encrypted) % 16))))[:len(self.encrypted)]
        else:
            self.decrypted = AES.new(self.key, AES.MODE_CBC, self.iv).decrypt(self.encrypted)
    def encrypt(self):
        if len(self.decrypted) % 16 != 0:
            self.encrypted = AES.new(self.key, AES.MODE_CBC, self.iv).encrypt(self.decrypted + ("\x00" * (16 - (len(self.decrypted) % 16))))
        else:
            self.encrypted = AES.new(self.key, AES.MODE_CBC, self.iv).encrypt(self.decrypted)

class WAD:
    def __init__(self, filename):
        self._f = open(filename, 'rb')
        self.headersize, self.wadtype, self.certsize, self.reserved, self.tiksize, self.tmdsize, self.datasize, self.footersize = struct.unpack('>I4s6I', self._f.read(32))
        self._f.seek(32, 1)
        self.rawcert = self._f.read(self.certsize)
        self.cert = self.rawcert
        if self.certsize % 64 != 0:
            self._f.seek(64 - (self.certsize % 64), 1)
        self.rawtik = self._f.read(self.tiksize)
        self.ticket = Ticket(self.rawtik)
        if self.tiksize % 64 != 0:
            self._f.seek(64 - (self.tiksize % 64), 1)
        self.rawtmd = self._f.read(self.tmdsize)
        self.tmd = TMD(self.rawtmd)
        if self.tmdsize % 64 != 0:
            self._f.seek(64 - (self.tmdsize % 64), 1)
        self.apps = []
        for self._i in range(0, self.tmd.contnum):
            self._tmpsize = self.tmd.contents[self._i].size
            if self._tmpsize % 16 != 0:
                self._tmpsize += 16 - (self._tmpsize % 16)
            self.apps.append(APP(self._f.read(self._tmpsize), self.ticket.titlekey, struct.pack(">H", self.tmd.contents[self._i].index) + "\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"))
            self.apps[self._i].decrypt()
            if self._tmpsize % 64 != 0:
                self._f.seek(64 - (self._tmpsize % 64), 1)
        self.timestamp = self._f.read(self.footersize)
        self._f.close()

    def pack(self):
        self._pack = struct.pack('>I4s6I', self.headersize, self.wadtype, self.certsize, self.reserved, self.tiksize, self.tmdsize, self.datasize, self.footersize)
        self._pack += "\x00" * 32
        self._pack += self.rawcert
        if len(self._pack) % 64 != 0:
            self._pack += "\x00" * (64 - (len(self._pack) % 64))
        self._pack += self.ticket.pack()
        if len(self._pack) % 64 != 0:
            self._pack += "\x00" * (64 - (len(self._pack) % 64))
        self._pack += self.tmd.pack()
        if len(self._pack) % 64 != 0:
            self._pack += "\x00" * (64 - (len(self._pack) % 64))
        for app in self.apps:
            self._pack += app.encrypted
            if len(self._pack) % 64 != 0:
                self._pack += "\x00" * (64 - (len(self._pack) % 64))
        self._pack += self.timestamp
        self._pack += "\x00" * (64 - len(self.timestamp) % 64)
        return self._pack




def update(directory):
    os.chdir(directory)
    tmd = TMD(open('tmd', 'rb').read())
    for content in tmd.contents:
        app = open("%08x.app" % content.index, 'rb').read()
        content.size = len(app)
        content.hash = hashlib.sha1(app).digest()
    tmd.fakesign()
    tmd.fixpayload()
    open('tmd', 'wb').write(tmd.pack())

def extract(filename,output=""):
    wad = WAD(filename)
    if output != "":
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

def packdir(directory,output=""):
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
    if output != "":
        open(output, 'wb').write(pack)
    else:
        open("%016x.wad" % ticket.titid, 'wb').write(pack)
