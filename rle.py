import pyglet.image


# Returns an ImageData
def rle_decode(width, height, encoded_data):
    res = ""
    in_pos = 0; in_len = len(encoded_data)
    out_pos = 0
    #x = 0; y = 0
    while in_pos < in_len and out_pos < width*height:
        d = ord(encoded_data[in_pos]); in_pos+=1
        if d >= 128:
            run_length = 257-d
            v = encoded_data[in_pos]; in_pos+=1
            for i in range(run_length): res += v
            out_pos += run_length
        else:
            lit_length = 1+d
            res += encoded_data[in_pos:in_pos+lit_length]; in_pos += lit_length
            out_pos += lit_length
    print "DB| rle end: out_pos: %d vs. expected %d; in_pos: %d vs. %d" % (out_pos, width*height, in_pos, in_len)
    #print "DB| rle: converted %s to %s" % (encoded_data, res)
    return pyglet.image.ImageData(width, height, 'I', res, -width)


