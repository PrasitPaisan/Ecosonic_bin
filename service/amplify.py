import numpy as np
import librosa
import soundfile as sf

def amplify_audio(input_file):
    # โหลดไฟล์เสียง
    y, sr = librosa.load(input_file, sr=None)
    
    max_val = np.max(np.abs(y))

    if max_val > 0:
        y_new = (1.0 /max_val) * y
    else:
        y_new = y

    
    output_path = './temp_output_amp.wav'

    sf.write(output_path, y_new, sr)
    print("Amplified audio saved to:", output_path)

    return output_path
 