#!/usr/bin/python

import sys
import struct

class SeqBuffer:  #------------------------------
    def __init__(self,src):
        self.buf = buffer(src)
        self.offset = 0

    def unpack(self,fmt):
        if isinstance(fmt,str): fmt=struct.Struct(fmt) # sic
        res = fmt.unpack_from(self.buf, self.offset)
        self.offset += fmt.size
        return res

    def at_eof(self):
        return self.offset >= len(self.buf)
#--------------------------------------------------

class MmapEntry:  #------------------------------
    def __init__(self,tag,size,offset):
        self.tag = tag
        self.size = size
        self.offset = offset

    def __repr__(self):
        return('MmapEntry(%s @%d+%d)' % (self.tag,self.offset,self.size))

    def read_from(self,file):
        file.seek(self.offset)
        xheader = file.read(8)
        [tag,size] = struct.unpack('!4si', xheader)
        if tag != self.tag:
            raise ("section header is actually %s, not %s as expected" % (tag, self.tag))
        return file.read(self.size)
#--------------------------------------------------

class Mmap: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    def append(self,item):
        self.entries.append(item)

    def find_entry_by_tag(self, tag):
        for e in self.entries:
            if e.tag == tag:
                return e
        return None

    @staticmethod
    def parse(xcontents):
        buf = SeqBuffer(xcontents)
        [v1,v2,nElems,nUsed,junkPtr,v3,freePtr] = \
        buf.unpack('>HHiiiii')
        print("mmap header: %s" % [v1,v2,nElems,nUsed,junkPtr,v3,freePtr])

        res = Mmap()
        while not buf.at_eof():
            [tag, size, offset, w1,w2, link] = \
                                               buf.unpack('>4sIIhhi')
            #print("mmap entry: %s" % [tag, size, offset, w1,w2, link])
            res.append(MmapEntry(tag, size, offset))
        return res


#--------------------------------------------------

def load_file(filename):
    with open(filename) as f:
        xheader = f.read(12)
        [magic,size,tag] = struct.unpack('!4si4s', xheader)
        if not (magic=="RIFX" and tag=="MV93"): raise "bad file type"
        mmap = find_and_read_section(f, "mmap")
        keys_e = mmap.find_entry_by_tag("KEY*")
        cast_e = mmap.find_entry_by_tag("CAS*")
        #print("mmap=%s" % mmap)
        print "Key sections: %s %s" % (keys_e, cast_e)
        print "Key sections data: keys: %s" % (keys_e.read_from(f))
        print "Key sections data: cast: %s" % (cast_e.read_from(f))
        print "OK"

def find_and_read_section(f, tag_to_find):
    while True:
        xheader = f.read(8)
        [tag,size] = struct.unpack('!4si', xheader)
        print("  tag=%s" % tag)
        if tag==tag_to_find:
            xcontents = f.read(size)
            return Mmap.parse(xcontents)
        else:
            f.seek(size, 1)

load_file(sys.argv[1])
