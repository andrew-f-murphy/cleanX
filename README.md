<p align="center">
<img style="width: 30%; height: 30%" src="https://github.com/drcandacemakedamoore/cleanX/blob/main/test/cleanXpic.png">
</p>

# cleanX

CleanX <a href="https://doi.org/10.5281/zenodo.4725904"><img src="https://zenodo.org/badge/DOI/10.5281/zenodo.4725904.svg" alt="(DOI)"></a> 
<a href="https://github.com/drcandacemakedamoore/cleanX/blob/master/LICENSE"><img alt="License: GPL-3" src="https://img.shields.io/github/license/drcandacemakedamoore/cleanX"></a>
is an open source python library
for exploring, cleaning and augmenting large datasets of Xrays as JPEG files.
(JPEG files can be extracted from DICOM files.)


### The latest official release:

<a href="https://pypi.org/project/cleanX/"><img alt="PyPI" src="https://img.shields.io/pypi/v/cleanX"></a>


primary author: Candace Makeda H. Moore

other authors + contributors: Oleg Sivokon, Andrew Murphy

## Continous Integration (CI) status

![ci workflow](https://github.com/drcandacemakedamoore/cleanX/actions/workflows/on-commit.yml/badge.svg)
![ci workflow](https://github.com/drcandacemakedamoore/cleanX/actions/workflows/on-tag.yml/badge.svg)


## Requirements

- a [python](https://www.python.org/downloads/) installation
- ability to create virtual environments (reccomended, not absolutely neccesary)
- tesseract-ocr and opencv
- anaconda is now supported, but not technically neccesary


## Documentation

Online documentation at https://drcandacemakedamoore.github.io/cleanX/

We encourage you to build up-to-date documentation by command.

Documentation can be generated by command:

``` sh
python setup.py apidoc
python setup.py build_sphinx
```

The documentation will be generated in `./build/sphinx/html` directory. Documentation is generated
automatically as new functions are added.  

# Installation
- setting up a virtual environment is desirable, but not absolutely neccesary

- activate  the environment
### Anaconda Installation

- use command for conda as below

        conda install -c doctormakeda -c conda-forge cleanx       

You need to specify both channels because there are some cleanX
dependencies that exist in both Anaconda main channel and in
conda-forge

### pip installation
- use pip as below

        pip install cleanX
    
    

## About using this library
If you use the library, please credit me and my collaborators.  You are only free to use this library according to license. We hope that if you use the library you will open source your entire code base, and send us modifications.  You can get in touch with me by email (doctormakeda@gmail.com) if you have a legitamate reason to use my library without open-sourcing your code base, or following other conditions, and I can make you specifically a different license.

We are adding new functions all the time. Some unit tests are availalable in the test folder. Test coverage is currently partial. The library includes many functions. Some newly added functions allow for rapid automated data augmentation (in ways that are realistic for X-rays). Some other functions are for cleaning datasets including ones that: 


### Run on dataframes to make sure there is no image leakage: 

check_paths_for_group_leakage(train_df, test_df, uniqueID):

    """
    Args:
        train_df (dataframe): dataframe describing train dataset
        test_df (dataframe): dataframe describing test dataset
        uniqueID (str): string name of column with image ID, patient IDs or some other unique ID that is in all dfs
    
    Returns:
        pics_in_both_groups: duplications of any image into both sets as a new dataframe
    """
    
    
### Crop off excessive black frames (run this on single images) one at a time:

simpler_crop(image):

     """
    Args:
        
        image: an image 
    
    Returns:
        image[np.min(y_nonzero):np.max(y_nonzero), np.min(x_nonzero):np.max(x_nonzero)]: image cropped of black edges
    """
    
### crop(image):

     """
    NB: expanded from simpler crop to handle for PIl and nonPIl types of JPEGS
    Args:
        
        image: an image 
    
    Returns:
        image[np.min(y_nonzero):np.max(y_nonzero), np.min(x_nonzero):np.max(x_nonzero)]: image cropped of black edges
    """
       
### Run on a list to make a prototype tiny Xray others can be comapared to: 


seperate_image_averger(set_of_images, s=5 ):

    """
    Args:
        
        set_of_images: a list 
        s: number of pixels for height and wifth
    
    Returns:
        canvas/len(set_of_images): an average tiny image (can feed another function which compares to this mini)
    """
    
### Run on image files which are inside a folder to check if they are "clean":

augment_and_move(origin_folder, target_folder, transformations):
    
    """
    Args:
        origin_folder: folder with 'virgin' images
        target_folder: folder to drop images after transformations
        transformations : example tranformations = [ImageOps.mirror, ImageOps.flip]...some function to transform the image
    
    Returns:
        technically not a return but puts augmented images into a new folder
    """

crop_them_all(origin_folder, target_folder):

    """
    Args:
        origin_folder: folder with 'virgin' images
        target_folder: folder to drop images after transformations
        
    
    Returns:
        technically not a return, but puts cropped images into target folder
    """
   


find_by_sample_upper(source_directory, percent_height_of_sample,  value_for_line):
 
    """

    function that takes top (upper percent) of images and checks if average pixel value is above value_for_line
        """         

find_sample_upper_greater_than_lower(source_directory, percent_height_of_sample):
 
    """
    function that checks that upper field (cut on percent_height of sample) of imagae has a higher pixel value than the lower field (it should in a typical CXR)
     
    """
    
def find_outliers_by_total_mean(source_directory, percentage_to_say_outliers):

        """
        Args:
        source_directory: directory with image files (should be more than 20)
        percentage_to_say_outliers: a number which will be the percentage of images contained in 
        the high mean and low mean sets
    
        Returns:
        lows,highs: images with low mean, images with high mean
        """
        


find_outliers_by_mean_to_df(source_directory, percentage_to_say_outliers):

        """
        Important note: approximate, and it can by chance cut the group so images with 
        the same mean are in and out of normal range if the knife so falls
        
        Args:
        source_directory: directory with image files (should be more than 20)
        percentage_to_say_outliers: a number which will be the percentage of images contained in 
        the high mean OR low mean sets- note if you set to 50, then all images will be high or low
    
        Returns:
        lows,highs: images with low mean, images with high mean into a dataframe
        """
        


find_tiny_image_differences(directory, s=5, percentile=8): 

    """
    Note: percentile returned is approximate, may be a tad more 
    Args:
        directory: directory of all the images you want to compare
        s: size of image sizes to compare
        percentile: what percentage you want to return
    Returns:
        difference_outliers: outliers in terms of difference from an average image
    """
      

tesseract_specific(directory):

 
    """this function runs tessseract ocr for text detection over images in a directory, and gives a dataframe with what it found"""
   

find_suspect_text(directory, label_word):
 
    """finds a specific string you believe is a label e.g. "cancer"  , this function looks for one single string in texts (multilingual!) on images

     
    """

find_suspect_text_by_legnth(directory, legnth):
 
    """
     this function finds all texts above a specified legnth (number of charecters)
      
    """
   
histogram_difference_for_inverts(directory):
 
    """
     this function looks for images by a spike on the end of pixel value histogram to find inverted images
      
    """
          
histogram_difference_for_inverts_todf(directory):


     """
     this function looks for images by a spike on the end of pixel value histogram to find inverted images, puts results in a dataframe
      
    """
    

find_duplicated_images(directory):
 
    """
     this function finds duplicated images and return a list
      
    """
   
find_duplicated_images_todf(directory):
 
    """
     looks for duplicated images, returns dataframe
     
    """

### Take a dataframe with image names and return plotted(visualized) images:

show_images_in_df(iter_ob, legnth_name):

    """
    Args:
        iter_ob: should be list(df.column)
        legnth_name: size of image name going from end
    Returns: plot of images with names    
        """
    

### Run to make a dataframe of pics in a folder (assuming they all have the same 'label'/diagnosis):

def dataframe_up_my_pics(directory, diagnosis_string):

    """
    Args:
        directory: directory/folder with images
        diagnosis_string: label column label
    Returns:
        ddataframe    
