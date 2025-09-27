import librosa
import shutil
import os
from PIL import Image
from tensorflow.keras.models import load_model
import sounddevice as sd
from scipy.io.wavfile import write
import time
import numpy as np
import cv2

from service.cut_sound import cut_sound_per_action
from service.cut_sound_splite_on_silence import cut_sound_per_action_split_on_silence
from utils.plot_compare import plot_compare
from service.converting_sound_to_mel_image import sound_to_image, sound_to_image_mel_mfcc
from service.redution import reduce_audio_noise
from utils.preprocess_the_image import convert_to_array
from sensor.servo_control import set_angle, cleanup
from sensor.stepper_controls import setup_gpio, motor_control, reset_motors_position
from sensor.LED_status import LED_status_color
from sensor.Ultrasonic_control import DropPassDetector      # <-- add this
from service.amplify import amplify_audio

Image.MAX_IMAGE_PIXELS = None
SAMPLE_RATE = 22050
n_fft = 2048
n_mels = 128
n_mfcc = 20
hop_length = 512          
target_size = (224, 224)

def process_and_predict(this_class_idx, amplified_path, input_path, sample_rate):
    check_action = cut_sound_per_action(amplified_path, "./results/sound", sample_rate)
    if not check_action:
        print("No actions detected, skipping processing.")
        safe_remove(amplified_path)
        safe_remove(input_path)
        time.sleep(0.2)
        return None

    sound_to_image_mel_mfcc_pre(
        dataset_path="./results/sound",
        output_path="./bottle",
        class_name="bottle",
        no = this_class_idx,
        n_mels=128, n_mfcc=20, n_fft=2048, hop_length=512
    )

def sound_to_image_mel_mfcc_pre(dataset_path, output_path,class_name,no,  n_mels=128, n_mfcc=20, n_fft=2048, hop_length=512):
    print(f"Converting sound to mel spectrogram imgage . . . {dataset_path}")
    for dirpath, dirnames, filenames in os.walk(dataset_path):
        for f in filenames:
                # ตรวจสอบเฉพาะไฟล์ที่เป็นเสียง (เช่น .wav หรือ .mp3)
                if f.endswith(('.wav', '.mp3')):
                    file_path = os.path.join(dirpath, f)
                    print(f"Converting file: {file_path} to Image")
                    
                    try:
                        y, sr = librosa.load(file_path,sr=22050)

                        # ===== Features =====
                        mel = librosa.feature.melspectrogram(y=y, sr=sr, n_mels=n_mels, n_fft=n_fft, hop_length=hop_length)
                        mel_db = librosa.power_to_db(mel, ref=np.max)

                        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length)

                        chroma = librosa.feature.chroma_stft(y=y, sr=sr, n_fft=n_fft, hop_length=hop_length)

                        # ===== Make time-frames equal (axis=1) =====
                        T = max(mel_db.shape[1], mfcc.shape[1], chroma.shape[1])
                        mel_db = librosa.util.fix_length(mel_db, size=T, axis=1)
                        mfcc   = librosa.util.fix_length(mfcc,   size=T, axis=1)
                        chroma = librosa.util.fix_length(chroma, size=T, axis=1)


                        # ===== Normalize to 0–255 (per-feature) =====
                        def norm255(x):
                            x = x.astype(np.float32)
                            x = cv2.normalize(x, None, 0, 255, cv2.NORM_MINMAX)
                            return x.astype(np.uint8)

                        # mel_img    = norm255(mel_db)
                        # mfcc_img   = norm255(mfcc)
                        # chroma_img = norm255(chroma)

                        # flip แนวตั้ง เพื่อให้แกน y อยู่ด้านล่างเหมือนภาพ spectrogram ปกติ in spacshow
                        mel_img    = np.flipud(norm255(mel_db))   # flip แนวตั้ง
                        mfcc_img   = np.flipud(norm255(mfcc))     # flip แนวตั้ง
                        chroma_img = np.flipud(norm255(chroma))   # flip แนวตั้ง


                        # ===== Resize =====
                        # mel/mfcc จะใช้ linear ก็ได้, แต่ chroma ใช้ NEAREST เพื่อให้แท่ง 12 แถวคม
                        mel_resized    = cv2.resize(mel_img,    target_size, interpolation=cv2.INTER_LINEAR)
                        mfcc_resized   = cv2.resize(mfcc_img,   target_size, interpolation=cv2.INTER_LINEAR)
                        chroma_resized = cv2.resize(chroma_img, target_size, interpolation=cv2.INTER_NEAREST)

                        # ===== Empty channel (optional) =====
                        empty_channel = np.zeros_like(mel_resized, dtype=np.uint8)

                        # ===== Stack to RGB =====
                        # ตัวอย่างนี้: เอาเฉพาะ chroma ในช่อง R ที่เหลือปิด (0)
                        rgb_image = np.stack([mel_resized, mfcc_resized, empty_channel], axis=-1)
                        # กำหนดชื่อประเภทและที่อยู่ไฟล์ภาพ
                        name_image = f.split('.')[0]
                        
                        # สร้างโฟลเดอร์ถ้ายังไม่มี
                        path_image = f'{output_path}/{class_name}_{no}.png'
                        os.makedirs(os.path.dirname(path_image), exist_ok=True)

                        # plt.savefig(path_image, bbox_inches='tight', pad_inches=0)
                        # plt.close()
                        Image.fromarray(rgb_image).save(path_image)
                        print(f"Saved image Finish: {path_image}")

                    except Exception as e:
                        print(f"Could not process {file_path}: {e}")




def safe_remove(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass

def cleanup_artifacts(amplified_path, input_path):
    shutil.rmtree('./results', ignore_errors=True)
    shutil.rmtree("./images", ignore_errors=True)
    for p in (amplified_path, input_path):
        safe_remove(p)

if __name__ == "__main__":
    detector = None
    this_class_idx = 3609
    try:
        LED_status_color("Red")
        sample_rate = 22050
        duration = 1.5  # sec

        setup_gpio()
        detector = DropPassDetector(TRIG=26, ECHO=25, NEAR_CM=17, FAR_CM_RELEASE=18, CYCLE_MS=12)

        print("System is ready, waiting for ultrasonic trigger...")

        while True:
            state = detector.read()
            LED_status_color("Red" if state == 0 else "Green")

            if state == 0:
                print("Detected !!")
                print(f"Recording for {duration} seconds...")
                recording = sd.rec(int(duration * sample_rate),
                                   samplerate=sample_rate, channels=1, dtype='float32')
                sd.wait()
                print("Recording complete!")
                input_path = "temp_input.wav"
                start_time = time.time()
                write(input_path, sample_rate, recording)

                amplified_path, sound_action = amplify_audio(input_path)
                if not sound_action:
                    print("No actions detected, skipping processing.")
                    safe_remove(input_path)
                    time.sleep(0.2)
                    continue

                process_and_predict(this_class_idx, amplified_path, input_path, sample_rate)
                set_angle(60)
                time.sleep(1)
                set_angle(0)

                # safe_remove(amplified_path)
                # safe_remove(input_path)
                shutil.rmtree('./results', ignore_errors=True)
                this_class_idx += 1
                
            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Exiting program")
        reset_motors_position()
        cleanup()
    finally:
        if detector is not None:
            detector.close()