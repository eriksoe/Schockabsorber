
#### Purpose:
# Defines a set of classes (some of them abstract) which give access
# to the sections of a .d*r file.
#

class SectionMap: #------------------------------
    def __init__(self, entries):
        self.entries = entries

    def __repr__(self):
        return repr(self.entries)

    def __getitem__(self,idx):
        return self.entries[idx]

    def entry_by_tag(self, tag):
        for e in self.entries:
            if e.tag == tag:
                return e
        return None
#--------------------------------------------------

class Section:  #------------------------------
    def __init__(self,tag,size,offset):
        self.tag = tag
        self.size = size
        self.offset = offset
        self.the_bytes = None

    def __repr__(self):
        return('MmapEntry(%s @%d+%d)' % (self.tag,self.offset,self.size))

    def bytes(self):
        if self.the_bytes==None:
            self.the_bytes = self.read_bytes()
        return self.the_bytes

    def read_bytes(self):
        raise NotImplementedError()
#--------------------------------------------------

