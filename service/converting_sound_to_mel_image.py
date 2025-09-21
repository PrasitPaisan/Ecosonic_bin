import os
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt
import cv2
from PIL import Image

SAMPLE_RATE = 22050
n_fft = 2048
n_mels = 128
n_mfcc = 20
hop_length = 512          # แก้จาก hope_length -> hop_length
target_size = (224, 224)

def sound_to_image_mel_mfcc(dataset_path, output_path, n_mels=n_mels,n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length):
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
                        path_image = f'{output_path}/{name_image}.png'
                        os.makedirs(os.path.dirname(path_image), exist_ok=True)

                        # plt.savefig(path_image, bbox_inches='tight', pad_inches=0)
                        # plt.close()
                        Image.fromarray(rgb_image).save(path_image)
                        print(f"Saved image Finish: {path_image}")

                    except Exception as e:
                        print(f"Could not process {file_path}: {e}")



def sound_to_image(dataset_path, output_path, n_mels=256, n_fft=2048, hop_length=256):
    print(f"Converting sound to mel spectrogram imgage . . . {dataset_path}")
    for dirpath, dirnames, filenames in os.walk(dataset_path):
        for f in filenames:
                # ตรวจสอบเฉพาะไฟล์ที่เป็นเสียง (เช่น .wav หรือ .mp3)
                if f.endswith(('.wav', '.mp3')):
                    file_path = os.path.join(dirpath, f)
                    print(f"Converting file: {file_path} to Image")
                    
                    try:
                        # โหลดไฟล์เสียง
                        signal, sample_rate = librosa.load(file_path, sr=SAMPLE_RATE)

                        # สร้าง mel spectrogram
                        mel_spectrogram = librosa.feature.melspectrogram(y=signal, sr=sample_rate, n_fft=n_fft, hop_length=hop_length, n_mels=n_mels)
                        
                        # convert mel to log scale (dB)
                        log_mel_spectrogram = librosa.power_to_db(mel_spectrogram, ref=np.max)

                        # สร้างภาพของ log mel spectrogram
                        plt.figure(figsize=(2.24, 2.24))
                        librosa.display.specshow(log_mel_spectrogram, sr=sample_rate, hop_length=hop_length, cmap='inferno')
                        plt.axis('off')
                        plt.tight_layout(pad=0)

                        # กำหนดชื่อประเภทและที่อยู่ไฟล์ภาพ
                        name_image = f.split('.')[0]
                        
                        # สร้างโฟลเดอร์ถ้ายังไม่มี
                        path_image = f'{output_path}/{name_image}.png'
                        os.makedirs(os.path.dirname(path_image), exist_ok=True)
                        # บันทึกภาพ
                        plt.savefig(path_image, bbox_inches='tight', pad_inches=0)
                        plt.close()  # ปิด plot เพื่อลดการใช้หน่วยความจำ
                        print(f"Saved image Finish: {path_image}")

                    except Exception as e:
                        print(f"Could not process {file_path}: {e}")

