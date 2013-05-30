
#### Purpose:
# Utilities for binary parsing.
#

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

    def unpackString8(self):
        [len] = self.unpack('B')
        str = self.buf[self.offset:self.offset+len]
        self.offset += len
        return str

    def bytes_left(self):
        return len(self.buf) - self.offset

    def at_eof(self):
        return self.offset >= len(self.buf)
#--------------------------------------------------
