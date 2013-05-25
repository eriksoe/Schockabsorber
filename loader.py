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

class MmapSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    def __getitem__(self,idx):
        return self.entries[idx]

    def find_entry_by_tag(self, tag):
        for e in self.entries:
            if e.tag == tag:
                return e
        return None

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        [v1,v2,nElems,nUsed,junkPtr,v3,freePtr] = buf.unpack('>HHiiiii')
        print("mmap header: %s" % [v1,v2,nElems,nUsed,junkPtr,v3,freePtr])

        res = MmapSection()
        while not buf.at_eof():
            [tag, size, offset, w1,w2, link] = buf.unpack('>4sIIhhi')
            #print("mmap entry: %s" % [tag, size, offset, w1,w2, link])
            res.entries.append(MmapEntry(tag, size, offset))
        return res
#--------------------------------------------------


class KeysSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        [v1,v2,nElems,v3] = buf.unpack('>HHii')
        print("KEY* header: %s" % [v1,v2,nElems,v3])

        res = KeysSection()
        while not buf.at_eof():
            [section_id, cast_id, tag] = buf.unpack('>ii4s')
            #print("mmap entry: %s" % [tag, size, offset, w1,w2, link])
            res.entries.append({"section_id":section_id,
                                "cast_id":cast_id,
                                "tag":tag})
        return res
#--------------------------------------------------

class CastTableSection: #------------------------------
    def __init__(self):
        self.entries = []

    def __repr__(self):
        return repr(self.entries)

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        res = CastTableSection()
        while not buf.at_eof():
            (item,) = buf.unpack('>i')
            res.entries.append(item)
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
        # print "Key sections data: keys: %s" % (keys_e.read_from(f))
        keys_section = KeysSection.parse(keys_e.read_from(f))
        # print "Key sections data: keys: %s" % (keys_section)
        # print "Key sections data: cast: %s" % (CastTableSection.parse(cast_e.read_from(f)))
        for e in keys_section.entries:
            tag = e["tag"]
            section_id = e["section_id"]
            section = mmap[section_id]
            cast_id = e["cast_id"]
            if cast_id != 0 and cast_id != 1024:
                cast_section = mmap[cast_id]
                print "  Key: %s: (%d)%s <-> (%d) %s" % (tag, section_id, section, cast_id, cast_section)
                cast_data = mmap[cast_id].read_from(f)
                [cast_type] = SeqBuffer(cast_data).unpack('>i')
                print "    Cast data (type %d): %s" % (cast_type,cast_data)
        print "OK"

def find_and_read_section(f, tag_to_find):
    while True:
        xheader = f.read(8)
        [tag,size] = struct.unpack('!4si', xheader)
        print("  tag=%s" % tag)
        if tag==tag_to_find:
            blob = f.read(size)
            return MmapSection.parse(blob)
        else:
            f.seek(size, 1)

load_file(sys.argv[1])
