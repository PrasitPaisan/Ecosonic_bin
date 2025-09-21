import numpy as np
import librosa
import soundfile as sf
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def amplify_audio(input_file, action_duration=400,silence_thresh=-45):
    # โหลดไฟล์เสียง
    output_path = './temp_output_amp.wav'

    sound = AudioSegment.from_wav(input_file)
    nonsilent_ranges = detect_nonsilent(sound, min_silence_len=action_duration, silence_thresh=silence_thresh)
    
    if not nonsilent_ranges:
        print("No sound detection in this file")
        return "" , False
    
    y, sr = librosa.load(input_file, sr=None)

    max_val = np.max(np.abs(y))
    max_target_rescale = .6
    if max_val > 0 and max_val < max_target_rescale:
        y_new = (max_target_rescale /max_val) * y
    else:
        y_new = y


    sf.write(output_path, y_new, sr)
    print("Amplified audio saved to:", output_path)

    return output_path,  True
 