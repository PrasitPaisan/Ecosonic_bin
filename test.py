import RPi.GPIO as GPIO
import time


DIR_PIN1 = 6   # ขาควบคุมทิศทาง
STEP_PIN1 = 24   # ขาควบคุมการหมุน (Step pulse)
DIR_PIN2 = 5   # ขาควบคุมทิศทาง
STEP_PIN2 = 23

# ตั้งค่าการทำงาน GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(DIR_PIN1, GPIO.OUT)
GPIO.setup(STEP_PIN1, GPIO.OUT)
GPIO.setup(DIR_PIN2, GPIO.OUT)
GPIO.setup(STEP_PIN2, GPIO.OUT)

# ตั้งทิศทางการหมุน (True = ตามเข็ม / False = ทวนเข็ม)
GPIO.output(DIR_PIN1, False)
GPIO.output(DIR_PIN2, False)

# จำนวน step ที่ต้องการ (ขึ้นกับโหมดไมโครสเต็ปด้วย)
step_count = 6400  # ถ้าใช้ 1/16 step → 3200 step = หมุนครบ 1 รอบ
step_delay = 0.00000001  # หน่วงเวลาแต่ละ step (เล็กลง = เร็วขึ้น)

try:
    for i in range(32):
        for _ in range(step_count):
            GPIO.output(STEP_PIN1, GPIO.HIGH)
            GPIO.output(STEP_PIN2, GPIO.HIGH)
            time.sleep(step_delay)
            GPIO.output(STEP_PIN1, GPIO.LOW)
            GPIO.output(STEP_PIN2, GPIO.LOW)
            time.sleep(step_delay)
finally:
    GPIO.cleanup()


# Predict the image grayscale
# =================================================================
img_size = (256, 256)
import tensorflow as tf
import numpy as np
from tensorflow import keras

# โหลดโมเดล
model = keras.models.load_model("my_model.h5")

img_path = "test.png"

# โหลดภาพเป็น grayscale และ resize
img = tf.keras.utils.load_img(img_path, color_mode="grayscale", target_size=img_size)
img_array = tf.keras.utils.img_to_array(img)  # shape (H,W,1)

# Normalize เหมือนตอน train (0-1)
img_array = img_array / 255.0

# เพิ่ม batch dimension -> (1, H, W, 1)
img_array = np.expand_dims(img_array, axis=0)

# predict
pred = model.predict(img_array)

# ถ้า label_mode='int' ใช้ softmax
pred_class = np.argmax(pred, axis=1)
print("Predicted class:", pred_class)

# ==================================================================