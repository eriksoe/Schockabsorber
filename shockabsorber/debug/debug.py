import pyglet
import shockabsorber.loader.rle

def print_castlibs(movie):
    for cl in movie.castlibs.iter_by_nr():
        print "==== Cast library \"%s\": ====" % (cl.name,)
        if cl.castmember_table==None: continue

        for i,cm in enumerate(cl.castmember_table):
            if cm==None: continue
            print "Cast table entry #%d: %s" % (i,cm)

def show_images(movie):
    images = []
    for cl in movie.castlibs.iter_by_nr():
        print "==== Cast library \"%s\": ====" % (cl.name,)
        if cl.castmember_table==None: continue

        for i,cm in enumerate(cl.castmember_table):
            if cm==None: continue
            print "%d: Loading image \"%s\"" % (i, cm.name)
            if not 'BITD' in cm.media: continue
            castdata = cm.castdata
            media = cm.media['BITD']
            (w,h) = castdata.dims
            (tw,th) = castdata.total_dims
            bpp = castdata.bpp
            image = shockabsorber.loader.rle.rle_decode(w,h, tw, bpp, media.data)
            images.append(image)
            if len(images)>50: break
    print "Image count: %d" % len(images)

    W = 5000; H = 1200
    window = pyglet.window.Window(width=W, height=H)

    @window.event
    def on_draw():
        window.clear()

        y = 0; x=0; maxw = 0
        for img in images:
            w = img.width
            h = img.height
            if y+h>=H:
                y = 0; x+= maxw + 20; maxw = 0
                if x>=W: break
            img.blit(x,y)
            if w>maxw: maxw = w
            y += h + 20

    pyglet.app.run()
