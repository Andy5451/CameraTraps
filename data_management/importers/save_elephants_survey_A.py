#
# save_elephants_survey_A.py
#
# Convert the .csv file provided for the Save The Elephants Survey A data set to a 
# COCO-camera-traps .json file
#

# %% Constants and environment

import pandas as pd
import os
import glob
import json
import re
import uuid
import time
import ntpath
import humanfriendly
import PIL
from PIL import Image
import numpy as np
import logging

input_metadata_file = r'/mnt/blobfuse/wildlifeblobssc/ste_2019_08_drop/SURVEY_A.xlsx'
output_file = r'/data/home/gramener/SURVEY_A.json'
image_directory = r'/mnt/blobfuse/wildlifeblobssc/ste_2019_08_drop/SURVEY A with False Triggers'
log_file = r'/data/home/gramener/save_elephants_survey_a.log'

assert(os.path.isdir(image_directory))
logging.basicConfig(filename=log_file, level=logging.INFO)


# %% Read source data

input_metadata = pd.read_excel(input_metadata_file, sheet_name='9. CT Image')
input_metadata = input_metadata.iloc[2:]

print('Read {} columns and {} rows from metadata file'.format(len(input_metadata.columns),
      len(input_metadata)))
# %% Map filenames to rows, verify image existence

# Takes ~30 seconds, since it's checking the existence of ~270k images

startTime = time.time()
filenamesToRows = {}
imageFilenames = input_metadata['Image Name']

duplicateRows = []

logging.info("File names which are present in CSV but not in the directory")
# Build up a map from filenames to a list of rows, checking image existence as we go
for iFile, fn in enumerate(imageFilenames):
    if (fn in filenamesToRows):
        # print(fn)
        duplicateRows.append(iFile)
        filenamesToRows[fn].append(iFile)
    else:
        filenamesToRows[fn] = [iFile]
        imagePath = os.path.join(image_directory, fn)
        try:
            assert(os.path.isfile(imagePath))
        except Exception:
            logging.info(imagePath)

elapsed = time.time() - startTime
print('Finished verifying image existence in {}, found {} filenames with multiple labels'.format(
      humanfriendly.format_timespan(elapsed), len(duplicateRows)))

# I didn't expect this to be true a priori, but it appears to be true, and
# it saves us the trouble of checking consistency across multiple occurrences
# of an image.
# assert(len(duplicateRows) == 0)    

# %% Check for images that aren't included in the metadata file

# Enumerate all images
imageFullPaths = glob.glob(os.path.join(image_directory, '*\\*\\*\\*.JPG'))
for iImage, imagePath in enumerate(imageFullPaths):
    # fn = ntpath.basename(imagePath)
    fn = imagePath.split(image_directory)[1]
    # parent_dir = os.path.basename(os.path.dirname(imagePath))
    assert(fn[1:] in filenamesToRows)

print('Finished checking {} images to make sure they\'re in the metadata'.format(
        len(imageFullPaths)))

# %% Create CCT dictionaries

# Also gets image sizes, so this takes ~6 minutes
#
# Implicitly checks images for overt corruptness, i.e. by not crashing.

images = []
annotations = []

# Map categories to integer IDs (that's what COCO likes)
nextCategoryID = 0
categoriesToCategoryId = {}
categoriesToCounts = {}

# For each image
#
# Because in practice images are 1:1 with annotations in this data set,
# this is also a loop over annotations.

startTime = time.time()
# print(imageFilenames)
# imageName = imageFilenames[0]
for imageName in imageFilenames:
    try:
        rows = filenamesToRows[imageName]
        iRow = rows[0]
        row = input_metadata.iloc[iRow+2]
        im = {}
        im['id'] = imageName.split('.')[0]
        im['file_name'] = imageName
        im['datetime'] = row['Date']
        im['Camera Trap Station Label'] = row['Camera Trap Station Label']
        if row['Photo Type '] is np.nan:
            im['Photo Type '] = ""
        else:
            im['Photo Type'] = row['Photo Type ']
        # Check image height and width
        imagePath = os.path.join(image_directory, imageName)
        assert(os.path.isfile(imagePath))
    except Exception:
        continue
    pilImage = Image.open(imagePath)
    width, height = pilImage.size
    im['width'] = width
    im['height'] = height

    images.append(im)
    
#     category = row['label'].lower()
    is_image = row['Species']
    
    # Use 'empty', to be consistent with other data on lila    
    if (is_image == np.nan):
        category = 'empty'
    else:
        category = row['Species']
        
    # Have we seen this category before?
    if category in categoriesToCategoryId:
        categoryID = categoriesToCategoryId[category]
        categoriesToCounts[category] += 1
    else:
        categoryID = nextCategoryID
        categoriesToCategoryId[category] = categoryID
        categoriesToCounts[category] = 0
        nextCategoryID += 1
    
    # Create an annotation
    ann = {}
    
    # The Internet tells me this guarantees uniqueness to a reasonable extent, even
    # beyond the sheer improbability of collisions.
    ann['id'] = str(uuid.uuid1())
    ann['image_id'] = im['id']    
    ann['category_id'] = categoryID
    
    annotations.append(ann)
    
# ...for each image
    
# Convert categories to a CCT-style dictionary

categories = []

for category in categoriesToCounts:
    print('Category {}, count {}'.format(category,categoriesToCounts[category]))
    categoryID = categoriesToCategoryId[category]
    cat = {}
    cat['name'] = category
    cat['id'] = categoryID
    categories.append(cat)    
    
elapsed = time.time() - startTime
print('Finished creating CCT dictionaries in {}'.format(
      humanfriendly.format_timespan(elapsed)))
    

# %% Create info struct

info = {}
info['year'] = 2014
info['version'] = 1
info['description'] = 'COCO style database'
info['secondary_contributor'] = 'Converted to COCO .json by Dan Morris'
info['contributor'] = 'Vardhan Duvvuri'


# # %% Write output

json_data = {}
json_data['images'] = images
json_data['annotations'] = annotations
json_data['categories'] = categories
json_data['info'] = info
json.dump(json_data, open(output_file, 'w'), indent=4)

print('Finished writing .json file with {} images, {} annotations, and {} categories'.format(
        len(images),len(annotations),len(categories)))
