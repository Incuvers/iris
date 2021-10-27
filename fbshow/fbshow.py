import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
class FrameBufShow:

    def __init__(self, output_device):
        self.output_device=output_device
        # these are hard-coded for IRIS's screen
        self.height=576
        self.width=1024
        # if we don't want text, a simple nparray will suffice (and we can boot PIL)
        #self.img=np.ones(shape=(self.height, self.width,4), dtype=np.uint8)*128
        self.img = Image.new('RGBA', (self.height, self.width), color = (66,66,66))

    def draw_text(self, text, coords=(288,512)):
        # file should be in same path relative to this script
        path = Path(__file__).parent.joinpath('Roboto-Regular.ttf')
        font = ImageFont.truetype(str(path), 20)
        imdraw = ImageDraw.Draw(self.img)
        imdraw.text(coords, text, fill=(255,255,255), anchor='mm', font=font)

    def show(self, text=None):
        # reset the image
        self.img = Image.new('RGBA', (self.height, self.width), color = (66,66,66))
        if text is not None:
            self.draw_text(text)
        with open(self.output_device, 'rb+') as buf:
            buf.write(np.asarray(self.img.getdata(),dtype=np.uint8))

if __name__ == "__main__":
    fb = FrameBufShow('/dev/fb0')
    fb.show()
