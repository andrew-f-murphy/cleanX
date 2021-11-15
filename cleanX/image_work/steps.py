# -*- coding: utf-8 -*-

import logging
import os
import json
import inspect

import numpy as np
import cv2


_known_steps = {}


def get_known_steps():
    return dict(_known_steps)


class RegisteredStep(type):
    def __init__(cls, name, bases, clsdict):
        if len(cls.mro()) > 2:
            _known_steps[cls.__name__] = cls
        super().__init__(name, bases, clsdict)


class Step(metaclass=RegisteredStep):
    """
    This class has default implementations for methods all steps are
    expected to implement.

    Use this as the base class if you intend to add custom steps.
    """

    def __init__(self, cache_dir=None):
        """
        If you extend this class, you need to call its :code:`__init__`.
        """
        self.cache_dir = cache_dir
        self.position = None

    def apply(self, image_data):
        """
        This is the method that will be called to do the actual image
        transformation.  This function must not raise exceptions, as it
        is used in the :mod:`multiprocessing` context.

        :param image_data: Will be the data obtained when calling
                           :meth:`~.Step.read()` method of this class.
        :type image_data: Unless this class overrides the defaults, this
                          will be :class:`~numpy.ndarray`.

        :return: This method should return two values.  First is the
                 processed image data.  This should be suitable for the
                 :meth:`~.Step.write()` method of this class to write.
                 Second is the error, if procesing wasn't possible.  Only
                 one element of the tuple should be :code:`not None`.
        :rtype: Tuple[numpy.ndarray, Exception]
        """
        return image_data, None

    def read(self, path):
        """
        Read the image saved in the previvous step.  This function must not
        raise exceptions as it is used in :code:`multiprocessing` context.

        :param path: The path to the image to read.  Unless the
                     :meth:`~.Step.write()` method of the previous step
                     was modified to do it differently, the format
                     of the data in the file is the serialized NumPy array

        :return: This method should return two values.  First is the
                 image data read from :code:`path`.  It should be in the
                 format suitable for :meth:`~.Step.apply()`.  Second is the
                 :class:`Exception` if the read was not successful.  Only
                 one element in the tuple may be :code:`not None`.
        :rtype: Tuple[numpy.ndarray, Exception]
        """
        try:
            res = np.load(path)
            return res, None
        except Exception as e:
            logging.exception(e)
            return None, e

    def write(self, image_data, path):
        """
        This method should write the image data to make it available for
        the next step.  Default implementation use NumPy's persistence
        format.  This method is used in :mod:`multiprocessing` context,
        therefore it must not raise exceptions.

        :param image_data: This is the result from calling
                           :meth:`~.Step.apply()` method of this class.
        :type image_data: Default implementation uses :class:`~numpy.ndarray`.
        :return: Exception if it was raised during the execution, or
                 :code:`None`.
        :rtype: Exception
        """
        try:
            assert image_data is not None, (
                'Image data should exist in {} at {}'.format(
                    type(self).__name__,
                    path,
                ))
            path = os.path.splitext(path)[0]
            np.save(path, image_data)
            return None
        except Exception as e:
            logging.exception(e)
            return e

    def __reduce__(self):
        return self.__class__, (self.cache_dir,)

    def to_json(self):
        result = {
            '__name__': type(self).__name__,
            '__module__': type(self).__module__,
        }
        names = inspect.getfullargspec(self.__init__)[0]
        values = self.__reduce__()[1]
        for k, v in zip(names, values):
            result[k] = v
        return json.dumps(result)

    @classmethod
    def from_cmd_args(cls, cmd_args):
        evaled_args = eval('dict({})'.format(cmd_args))
        return cls(**evaled_args)


class Acquire(Step):
    """This class reads in images (to an array) from a path"""

    def read(self, path):
        try:
            res = cv2.imread(path)
            return np.array(res), None
        except Exception as e:
            logging.exception(e)
            return None, e


class Save(Step):
    """This class writes the images somewhere"""

    def __init__(self, target, extension='jpg', cache_dir=None):
        super().__init__(cache_dir)
        self.target = target
        self.extension = extension

    def write(self, image_data, path):
        err = super().write(image_data, path)
        if err:
            return err
        name = '{}.{}'.format(
            os.path.splitext(os.path.basename(path))[0],
            self.extension,
        )
        try:
            cv2.imwrite(
                os.path.join(self.target, name),
                image_data,
            )
        except Exception as e:
            logging.exception(e)
            return e

    def __reduce__(self):
        return self.__class__, (
            self.target,
            self.extension,
            self.cache_dir,
        )


class Crop(Step):
    """This class crops image arrays of black frames"""

    def apply(self, image_data):

        try:
            nonzero = np.nonzero(image_data)
            y_nonzero = nonzero[0]
            x_nonzero = nonzero[1]
    # , x_nonzero, _ = np.nonzero(image)
            return image_data[
                np.min(y_nonzero):np.max(y_nonzero),
                np.min(x_nonzero):np.max(x_nonzero)
            ], None
        except Exception as e:
            logging.exception(e)
            return None, e

# class Tee(Step):
#     """This step makes duplicate images, then opens two parallel pipelines"""
        # Unfinished
#     def apply(self, image_data):


class Salt(Step):
    """This class takes the image and applies the salting function
    (augments with noise). In present version reccomended to run on copies.
    In future versions can be run after a Tee step"""

    def __init__(
        self,
        kernel=(5, 5),
        erosion_interations=90,
        dilation_iterations=10,
        cache_dir=None,
    ):
        super().__init__(cache_dir)
        self.kernel = kernel
        self.erosion_iterations = erosion_interations
        self.dilation_iterations = dilation_iterations

    def apply(self, image_data):
        erosion = cv2.erode(
            image_data,
            self.kernel,
            iterations=self.erosion_iterations,
        )
        dilation = cv2.dilate(
            erosion,
            self.kernel,
            iterations=self.dilation_iterations,
        )
        salty_noised = (image_data + (erosion - dilation))
        return salty_noised, None


class Sharpie(Step):
    """This class takes the image and applies a variant of thethe subtle
    sharpie  function, but with control over the degree. In present version,
    it is reccomended to run on copies.
    In future versions can be run after a Tee step. For a subtle sharpening
    a ksize of (2,2) is reccomended, and a run of normalization afterwards is 
    highly reccomended (or you may get vals over 255 for whites)"""

    def __init__(
        self,
        ksize=(2, 2),
        cache_dir=None,
    ):
        super().__init__(cache_dir)
        self.ksize = ksize

    def apply(self, image_data):
        blur_mask = cv2.blur(image_data, ksize=self.ksize)
        new_image_array = 2 * image_data - blur_mask
        return new_image_array, None


class BlurEdges(Step):
    """This class takes the image and applies a variant of thethe blur out
    edges  function, which does what it sounds like (returns an image with
    edges blurred out called edge_image). For a good effect a ksize of
    (600,600) is reccomended. In present version,it is reccomended to run on
    copies.In future versions can be run after a Tee step. """

    def __init__(
        self,
        ksize=(600, 600),
        cache_dir=None,
    ):
        super().__init__(cache_dir)
        self.ksize = ksize

    def apply(self, image_data):
        msk = np.zeros(image_data.shape)
        center_coordinates = (
            image_data.shape[1] // 2,
            image_data.shape[0] // 2,
        )
        radius = int(
            (min(image_data.shape) // 100) * (min(image_data.shape)/40)
        )
        color = 255
        thickness = -1
        msk = cv2.circle(msk, center_coordinates, radius, color, thickness)
        ksize = self.ksize
        msk = cv2.blur(msk, ksize)
        filtered = cv2.blur(image_data, ksize)
        edge_image = image_data * (msk / 255) + filtered * ((255 - msk) / 255)
        return edge_image, None


# class Rotate(Step):
#     """This class takes the image and applies a rotation  function,
#     with control over the degree. In present version, it is reccomended to 
#     run on copies. In future versions can be run after a Tee step.
#     UNDER DEVELOPMENT """

#     def __init__(
#         self,
#         angle=2,
#         center=
#         scale=
#         cache_dir=None,
#     ):
#         super().__init__(cache_dir)
#         self.angle = angle

#     def apply(self, image_data):
#         matrix = cv2.getRotationMatrix2D(self.center, angle, self.scale)
#         rotated = cv2.warpAffine(image_data, matrix, (image_data.shape[0], image_data.shape[1]))
#         return rotated, None


class Normalize(Step):
    """This class makes a simple normalizing to get values 0 to 255."""

    def apply(self, image_data):
        try:
            new_max_value = 255

            max_value = np.amax(image_data)
            min_value = np.amin(image_data)

            img_py = image_data - min_value
            multiplier_ratio = new_max_value/max_value
            img_py = img_py*multiplier_ratio
            return img_py, None
        except Exception as e:
            logging.exception(e)
            return None, e


class HistogramNormalize(Step):
    """This class allows normalization by throwing off exxtreme values on
    image histogram. """

    def __init__(self, tail_cut_percent=5, cache_dir=None):
        super().__init__(cache_dir)
        self.tail_cut_percent = tail_cut_percent

    def apply(self, image_data):
        try:
            new_max_value = 255
            img_py = np.array((image_data), dtype='int64')
            # num_total = img_py.shape[0]*img_py.shape[1]
            # list_from_array = img_py.tolist()
            gray_hist = np.histogram(img_py, bins=256)[0]
            area = gray_hist.sum()
            cutoff = area * (self.tail_cut_percent/100)
            dark_cutoff = 0
            bright_cutoff = 255
            area_so_far = 0
            for i, b in enumerate(gray_hist):
                area_so_far += b
                if area_so_far >= cutoff:
                    dark_cutoff = max(0, i - 1)
                    break
            area_so_far = 0
            for i, b in enumerate(reversed(gray_hist)):
                area_so_far += b
                if area_so_far >= cutoff:
                    bright_cutoff = min(255, 255 - i)
                    break

            img_py = img_py - dark_cutoff
            img_py[img_py < 0] = 0
            max_value2 = np.amax(img_py)
            # min_value2 = np.amin(img_py)
            multiplier_ratio = new_max_value/max_value2
            img_py = img_py*multiplier_ratio

            return img_py, None
        except Exception as e:
            logging.exception(e)
            return None, e

    def __reduce__(self):
        return self.__class__, (self.tail_cut_percent, self.cache_dir)
