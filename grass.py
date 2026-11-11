from pico2d import *

import os
path = os.getcwd() + '\\Labs\\LEC16_Time\\'

class Grass:
    def __init__(self):
        self.image = load_image(path + 'grass.png')
        self.ruler_image = load_image(path + 'ruler.png')

    def update(self):
        pass

    def draw(self):
        self.image.draw(400, 30)
        self.image.draw(1200, 30)
        self.ruler_image.draw(800, 350)
