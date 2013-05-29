#!/usr/bin/python

import sys
import struct
import zlib

class SeqBuffer:  #------------------------------
    def __init__(self,src):
        self.buf = buffer(src)
        self.offset = 0

    def unpack(self,fmt):
        if isinstance(fmt,str): fmt=struct.Struct(fmt) # sic
        res = fmt.unpack_from(self.buf, self.offset)
        self.offset += fmt.size
        return res

    def unpackString8(self):
        [len] = self.unpack('B')
        str = self.buf[self.offset:self.offset+len]
        self.offset += len
        return str

    def unpackVarint(self):
        d = ord(self.buf[self.offset])
        #print "DB| unpackVarint: %d" % d
        self.offset += 1
        if d<128:
            return d
        else:
            return ((d-128)<<7) | self.unpackVarint()

    def readBytes(self, len):
        bytes = self.buf[self.offset:self.offset+len]
        self.offset += len
        return bytes

    def bytes_left(self):
        return len(self.buf) - self.offset

    def at_eof(self):
        return self.offset >= len(self.buf)
#--------------------------------------------------

class MmapEntry:  #------------------------------
    def __init__(self,nr,tag,size,offset, repr_mode):
        self.nr = nr
        self.tag = tag
        self.size = size
        self.offset = offset
        self.repr_mode = repr_mode

    def __repr__(self):
        return('MmapEntry(%d %s @%d+%d)' % (self.nr, self.tag,self.offset,self.size))

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
        self.entries_by_nr = {}

    def __repr__(self):
        return repr(self.entries)

    def __getitem__(self,idx):
        return self.entries[idx]

    def get_by_nr(self,nr):
        return self.entries_by_nr[nr]

    def add(self, mmap_entry):
        self.entries.append(mmap_entry)
        self.entries_by_nr[mmap_entry.nr] = mmap_entry

    def find_entry_by_tag(self, tag):
        for e in self.entries:
            if e.tag == tag:
                return e
        return None

    @staticmethod
    def parse(blob):
        buf = SeqBuffer(blob)
        #[v1,v2,nElems,nUsed,junkPtr,v3,freePtr] = buf.unpack('<HHiiiii')
        #print("mmap header: %s" % [v1,v2,nElems,nUsed,junkPtr,v3,freePtr])
        v1 = buf.unpackVarint()
        v2 = buf.unpackVarint()
        section_count = buf.unpackVarint()
        print("mmap header: %s" % [v1,v2, section_count])

        #w1sum=0; w2sum=0; w3sum=0; w4sum=0
        csum=0; usum=0
        res = MmapSection()
        for i in range(section_count):
            id = buf.unpackVarint()
            offset = buf.unpackVarint() # offset
            comp_size = buf.unpackVarint() # size in file
            decomp_size = buf.unpackVarint() # size, decompressed
            repr_mode = buf.unpackVarint()
            [tag] = buf.unpack('<4s')
            tag = rev(tag)
            print("mmap entry: %s" % ([id, tag,
                                               offset, comp_size, decomp_size,
                                               repr_mode]))
            res.add(MmapEntry(id, tag, comp_size, offset, repr_mode))

            # if w1!=0x3fff:
            #     usum += w2
            # else:
            #     csum += w2+1
            #     #w1sum += w1; w2sum += w2; w3sum += w3; w4sum += w4
        print "Bytes left in mmap section: %d" % buf.bytes_left()
        # print "Sums: %s" % [csum, usum]
        return res
#--------------------------------------------------

def load_file(filename):
    with open(filename) as f:
        xheader = f.read(12)
        [magic,fsize,tag] = struct.unpack('<4si4s', xheader)
        magic = rev(magic)
        tag = rev(tag)
        print "DB| magic=%s tag=%s" % (magic,tag)
        if not (magic=="RIFX" and tag=="FGDM"): raise "bad file type"

        while True:
            xsectheader = f.read(4)
            if len(xsectheader) < 4: break
            [stag] = struct.unpack('<4s', xsectheader)
            stag = rev(stag)
            ssize = read_varint(f)
            print "stag=%s ssize=%d" % (stag, ssize)
            if ssize==0:
                break
            else:
                sect_data = f.read(ssize)
            if stag == "Fcdr" or stag == "FGEI":
                sect_data = zlib.decompress(sect_data)
                print "ssize decompressed=%d" % (len(sect_data))
            elif stag == "ABMP":
                sect_data = zlib.decompress(sect_data[3:])
                print "ssize decompressed=%d" % (len(sect_data))
                mmap = MmapSection.parse(sect_data)
                print "DB| mmap: %s" % mmap
            print "DB| %s -> %s" % (stag, sect_data)
        sections_data_base = f.tell()

        # Fetch the sections:
        sections = {}
        #comp_source = None
        for snr in mmap.entries_by_nr:
            e = mmap.get_by_nr(snr)
            print "DB| section nr %s: %s" % (snr,e)
            if e.offset == 0x3fff:
                # Compressed.
                #sdata = comp_source[e.offset:e.offset+e.size]
                "dummy"
            else:
                f.seek(sections_data_base + e.offset)
                raw_sdata = f.read(e.size)
                if e.repr_mode==0:
                    sdata = zlib.decompress(raw_sdata)
                elif e.repr_mode==1:
                    sdata = raw_sdata
                else:
                    raise "unknown repr_mode: %d" % e.repr_mode
                sections[snr] = (e.tag,sdata)
                if e.tag=="ILS ":
                    #comp_source = sdata
                    read_ILS_section_into(sdata, mmap, sections)
        print "Sections=%s" % (sections.keys())
        print "Sections:"
        for snr in sections:
            print "  %d: %s" % (snr, sections[snr])
        # mmap = find_and_read_section(f, "mmap")
        # cast_table = create_cast_table(f,mmap)
        # print "==== cast_table: ===="
        # for cm in cast_table: print "  %s" % cm
        # return (cast_table,)

def read_ILS_section_into(ils_data, mmap, dest):
    buf = SeqBuffer(ils_data)
    while not buf.at_eof():
        snr = buf.unpackVarint()
        smeta = mmap.get_by_nr(snr)
        sdata = buf.readBytes(smeta.size)
        dest[snr] = (smeta.tag, sdata)

def rev(s):
    return s[::-1]

def read_varint(f):
    d = ord(f.read(1))
    if d<128:
        return d
    else:
        return ((d-128)<<7) + read_varint(f)

load_file(sys.argv[1])
