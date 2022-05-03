import cv2
import numpy as np
import os
import pandas as pd

from tqdm import tqdm
from glob import glob
from albumentations import RandomCrop, HorizontalFlip, VerticalFlip

from sklearn.model_selection import train_test_split
from PIL import Image

from tensorflow.keras.layers import Input, Conv2D, BatchNormalization, Activation, MaxPool2D, UpSampling2D, Concatenate
from tensorflow.keras.models import Model

import tensorflow as tf
import matplotlib.pyplot as plt
from tensorflow.keras.callbacks import ModelCheckpoint, ReduceLROnPlateau, EarlyStopping, Callback
from tensorflow.keras.utils import plot_model
import os

from utils.data_IO import (create_dir, create_dataframe)
from utils.data_preprocess import (read_image, read_mask, 
                                   tf_dataset, preprocess,
                                   augment_data)
from utils.models import mobileunet, unet
from utils.dimensions import Height, Width

# Show GPUs devices
from tensorflow.python.client import device_lib
print(device_lib.list_local_devices())


###############
### Data IO ###
###############

path = "../data/dataset/semantic_drone_dataset"
#images = sorted(glob(os.path.join(path, "original_images/*")))
#masks = sorted(glob(os.path.join(path, "label_images_semantic/*")))
#print(f"Original images:  {len(images)} - Original masks: {len(masks)}")

#create_dir("../data/dataset/semantic_drone_dataset/new_data/images/")
#create_dir("../data/dataset/semantic_drone_dataset/new_data/masks/")

save_path = "../data/dataset/semantic_drone_dataset/new_data/"

#augment_data(images, masks, save_path, augment=True)

images = sorted(glob(os.path.join(save_path, "images/*")))
masks = sorted(glob(os.path.join(save_path, "masks/*")))
print(f"Augmented images:  {len(images)} - Augmented masks: {len(masks)}")

# Create dataframe
image_path =  os.path.join(save_path, "images/")
label_path = os.path.join(save_path, "masks/")
df_images = create_dataframe(image_path)
df_masks = create_dataframe(label_path)
print('Total Images: ', len(df_images))
#print(df_images)

# Split data
X_trainval, X_test = train_test_split(df_images['id'], test_size=0.1, random_state=19)
X_trainval=df_images['id']
X_train, X_val = train_test_split(X_trainval, test_size=0.2, random_state=19)

print(f"Train Size : {len(X_train)} images")
print(f"Val Size   :  {len(X_val)} images")
print(f"Test Size  :  {len(X_test)} images")

y_train = X_train #the same values for images (X) and labels (y)
y_test = X_test
y_val = X_val

img_train = [os.path.join(image_path, f"{name}.jpg") for name in X_train]
mask_train = [os.path.join(label_path, f"{name}.png") for name in y_train]
img_val = [os.path.join(image_path, f"{name}.jpg") for name in X_val]
mask_val = [os.path.join(label_path, f"{name}.png") for name in y_val]
img_test = [os.path.join(image_path, f"{name}.jpg") for name in X_test]
mask_test = [os.path.join(label_path, f"{name}.png") for name in y_test]

####################
### Define Model ###
####################

# Define the resolution of the images and 
H = Height   
W = Width 
shape = (H, W, 3)

# Define the number of classes
num_classes = 23

# Hyperparameters
lr = 1e-4
batch_size = 4
epochs = 500

# Compile Model
# Try with higher learning rate: SGD, RMSprop
# Try doubling neuron number (doubling under performs on val accuracy), then half. 
#model.compile(loss="categorical_crossentropy", optimizer=tf.keras.optimizers.Adam(lr), metrics=['accuracy'])

n1 = 64/2
n2 = 128/2
n3 = 256/2
n4 = 512/2
n5 = 1024/2

# Define Unet model
#model = mobileunet(shape, num_classes, lr,  n1, n2, n3, n4, n5)
model = unet(shape, num_classes, lr)

# Display model summary
model.summary()
#plot_model(model,to_file='model.png')


###################
### Train Model ###
###################

# Seeding
np.random.seed(42)
tf.random.set_seed(42)


# Get dataset
train_dataset = tf_dataset(img_train, mask_train, batch_size)
valid_dataset = tf_dataset(img_val, mask_val, batch_size)

# Specify step size
train_steps = len(img_train)//batch_size
valid_steps = len(img_val)//batch_size

# Check points
checkpointer = [
    ModelCheckpoint(filepath="../results/models/model_14.h5",monitor='val_loss',verbose=2,save_best_only=True),
    ReduceLROnPlateau(monitor='val_loss', patience=3, factor=0.1, verbose=2, min_lr=1e-8),
    EarlyStopping(monitor='val_loss', patience=10, verbose=2)
]

# Train model
history = model.fit(train_dataset,
          steps_per_epoch=train_steps,
          validation_data=valid_dataset,
          validation_steps=valid_steps,
          epochs=epochs,
          callbacks=checkpointer
         )

# Plot training accuracy
plt.figure()
plt.plot(history.history['accuracy'])
plt.plot(history.history['val_accuracy'])
plt.title('Model Accuracy')
plt.ylabel('Accuracy')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper left')
plt.savefig("../results/residuals/accuracy.png")

# Plot training loss
plt.figure()
plt.plot(history.history['loss'])
plt.plot(history.history['val_loss'])
plt.title('Model Loss')
plt.ylabel('Loss')
plt.xlabel('Epoch')
plt.legend(['Train', 'Test'], loc='upper right')
plt.savefig("../results/residuals/loss.png")











