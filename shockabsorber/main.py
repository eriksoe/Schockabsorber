import sys
import shockabsorber.loader.loader
import shockabsorber.model.movie
from shockabsorber.debug import debug

# For now, this is just a test program showing the bitmap images in a file.
def main():
    movie = shockabsorber.loader.loader.load_movie(sys.argv[1])
    debug.print_castlibs(movie)
    debug.show_images(movie)
