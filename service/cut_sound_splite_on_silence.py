from pydub import AudioSegment
from pydub.silence import split_on_silence
import os 

def cut_sound_per_action_split_on_silence(input_path, output_dir, action_duration=400, length_duration=1000):
    print("Cutting sound per action . . . ")

    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    sound = AudioSegment.from_file(input_path)
    segments = split_on_silence(sound,
                                min_silence_len=action_duration,
                                silence_thresh=-40,
                                keep_silence=400)
    if not segments:
        print("No sound detection in this file")
        return 0
    
    for i, seg in enumerate(segments):
        if len(seg) < length_duration:
            silence_to_add = AudioSegment.silent(duration=length_duration - len(seg))
            seg += silence_to_add
        seg = seg[:length_duration]
        output_file = f"{output_dir}/value_{i + 1}.wav"
        seg.export(output_file, format="wav")
    print(f"Finished cutting sound per action , {len(segments)} actions")

    return 1
