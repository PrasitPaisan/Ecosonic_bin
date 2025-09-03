from tensorflow.keras.preprocessing import image
import numpy as np

def convert_to_array(image_path):
    img = image.load_img(image_path, target_size=(224,224))
    img_array = image.img_to_array(img)
    img_array = img_array /255.0
    img_array = np.expand_dims(img_array, axis=0)
    return img_array