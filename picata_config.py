import os

class PicataConfig:

    def __init__(self):
        self.path = os.getcwd()
        self.prefix =  "picata_"
        self.file_prefix = self.path + "/" + self.prefix
