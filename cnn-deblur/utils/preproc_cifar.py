import tensorflow as tf
import numpy as np
import cv2
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional


def preproc_subset(target: np.ndarray,
                   rnd: Optional[np.random.RandomState] = None) -> np.ndarray:
    """Function which, given the target composed of the clear images, computes the predictor by applying random
    gaussian blur
        :param target: set of clear images
        :param rnd: random state to ensure reproducible results (optional)

        :return predictor: set of blurred images"""
    subset_size = target.shape[0]

    # Function which blurs a given image with Gaussian blur
    # (standard deviation chosen randomly between 0 and 3)
    def gauss_blur(img):
        if rnd is not None:
            std_dev = rnd.uniform(0, 3)
        else:
            std_dev = np.random.uniform(0, 3)
        return cv2.GaussianBlur(src=img, ksize=(0, 0), sigmaX=std_dev, borderType=cv2.BORDER_DEFAULT)

    # Create predictor
    predictor = np.zeros(shape=target.shape, dtype=target.dtype)

    # Save in predictor the blurred version of the target
    for i in range(subset_size):
        predictor[i] = gauss_blur(target[i])

    return predictor


def preproc_cifar(normalize: Optional[bool] = False):
    """Function that loads Cifar10 dataset and produces a training and test set in which the predictors are randomly
    Gaussian blurred images and the targets are the clear version of such images
        :param normalize: boolean indicating whether the pixel values should be normalized between 0 and 1 (optional)

        :return train: tuple containing predictor and target images of the train set
        :return test: tuple containing predictor and target images of the test set"""

    # Load training and test sets from Cifar10 dataset (labels are ignored)
    (train_set, _), (test_set, _) = tf.keras.datasets.cifar10.load_data()

    # Set random state to ensure reproducible results
    rnd = np.random.RandomState(42)

    # Concurrently produce train and test sets
    trainX = None
    trainY = None
    testX = None
    testY = None
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=2) as executor:
        futureTrain = executor.submit(preproc_subset, train_set, rnd)
        futureTest = executor.submit(preproc_subset, test_set, rnd)
        futures = [futureTrain, futureTest]
        for future in as_completed(futures):
            if future == futureTrain:
                trainX = future.result()
                trainY = train_set
            else:
                testX = future.result()
                testY = test_set
    # Normalize if required
    if normalize:
        trainX = trainX.astype(np.float)/255
        trainY = trainY.astype(np.float)/255
        testX = testX.astype(np.float)/255
        testY = testY.astype(np.float)/255
    print('Time elapsed: {0:.2f} s'.format(time.time() - start_time))

    return (trainX, trainY), (testX, testY)
