import os


class PicataConfig:
    """ Picata configuration class, mostly for file paths """

    def __init__(self):
        """ Simple file path configuration for quiz data to be saved. """
        self.path = os.getcwd()
        self.prefix = "quiz_"
        self.file_prefix = self.path + "/" + self.prefix
