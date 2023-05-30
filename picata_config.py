import os

class PicataConfig:
    """ Picata configuration class, mostly for file paths """

    def __init__(self):
        self.path = os.getcwd()
        self.prefix =  "quiz_"
        self.file_prefix = self.path + "/" + self.prefix
