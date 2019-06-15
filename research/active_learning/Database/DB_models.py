'''
DB_models.py

Defines model classes representing database tables used in active learning for classification.

'''

from peewee import *
from enum import Enum

db_proxy = Proxy() # create a proxy backend for the database

class DetectionKind(Enum):
    ModelDetection = 0  # "output of the detection model"--i.e. a crop with no label? or a crop with a label guessed by the classifier?
    ActiveDetection = 1 # "selected for labeling by the oracle"--i.e. a crop currently flagged as needing a label?
    UserDetection = 2   # label has been assigned by the user


class Info(Model):
    '''
    Table containing information about the dataset.
    '''
    name = CharField() # name of dataset
    description = CharField()
    contributor = CharField()
    version = IntegerField()
    year = IntegerField()
    date_created = DateField()
    RM = FloatField(null = True, default= -1) # mean in RGB channels(?)
    GM = FloatField(null = True, default= -1)
    BM = FloatField(null = True, default= -1)
    RS = FloatField(null = True, default= -1) # standard deviation in RGB channels (?)
    GS = FloatField(null = True, default= -1)
    BS = FloatField(null = True, default= -1)

    class Meta:
        database = db_proxy


class Image(Model):
    '''
    Table containing information about each cropped image in the dataset.
    '''
    id = CharField(primary_key=True)    # cropped image unique identifier
    file_name = CharField()             # cropped image file name
    width = IntegerField(null = True)   # cropped image dimensions in pixels
    height = IntegerField(null= True)
    grayscale = BooleanField(null = True)   # whether the cropped image is grayscale
    relative_size = FloatField(null = True) # cropped image size relative to original image size   

    source_file_name = CharField()      # full image file name from which cropped image was generated
    seq_id = CharField(null= True)      # sequence identifier for the full image
    seq_num_frames = IntegerField(null = True)  # number of frames in sequence
    frame_num = IntegerField(null = True)       # which frame number in sequence
    location = CharField(null = True)   # location of camera trap
    datetime = DateTimeField(null = True)
    
    class Meta:
        database = db_proxy


class Category(Model):
    '''
    Table containing information about classes (species) in the dataset.
    '''
    id = IntegerField(primary_key=True)
    name = CharField()

    class Meta:
        database= db_proxy


class Detection(Model):
    '''
    Table containing information about detections (annotations) in the dataset.
    '''
    id = CharField(primary_key=True)    # detection unique identifier
    image = ForeignKeyField(Image)      # pointer to cropped image the detection corresponds to
    kind = IntegerField()               # numeric code representing what kind of detection this is
    category = ForeignKeyField(Category)    # label assigned to the detection
    category_confidence = FloatField(null= True)    # confidence associated with the detection

    class Meta:
        database = db_proxy
     
    

class Oracle(Model):
    '''
    Table containing information about labels for each detection in the dataset.
    '''
    detection = ForeignKeyField(Detection)
    label = IntegerField(null=True)

    class Meta:
        database = db_proxy    