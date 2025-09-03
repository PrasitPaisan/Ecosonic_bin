import os
import librosa
import librosa.display
import numpy as np
import matplotlib.pyplot as plt

SAMPLE_RATE = 22050

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

