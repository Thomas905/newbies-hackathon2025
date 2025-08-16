
import os.path as path
import pygame
import cv2 as cv
import numpy as np
import time
import mediapipe as mp
import random
import os
import setting

SCREEN_WIDTH = 450
SCREEN_HEIGHT = 720

print(__file__)
project_folder = path.dirname(__file__)

img_folder = path.join(project_folder,"entity")
snd_folder = path.join(project_folder,"entity")
print(img_folder)

