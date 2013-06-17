class CastLibraryTable: #------------------------------
    def __init__(self, castlibs):
        self.by_nr = {}
        self.by_assoc_id = {}
        for cl in castlibs:
            self.by_nr[cl.nr] = cl
            if cl.assoc_id>0:
                self.by_assoc_id[cl.assoc_id] = cl

    def iter_by_nr(self):
        return self.by_nr.itervalues()
#--------------------------------------------------

class CastLibrary: #------------------------------
    def __init__(self, nr, name, path, assoc_id, idx_range, self_idx):
        self.nr = nr
        self.name = name
        self.path = path
        self.assoc_id = assoc_id
        self.idx_range = idx_range
        self.self_idx = self_idx
        self.castmember_table = None

    def __repr__(self):
        return "<CastLibrary #%d name=\"%s\">" % (self.nr, self.name)

    def set_castmember_table(self,table):
        self.castmember_table = table
#--------------------------------------------------
