import numpy as np
from pydub import AudioSegment

def convert_to_2bytes(audio_data, sample_rate):

    audio_int16 = (audio_data * 32767).astype(np.int16)
    audio_bytes = audio_int16.tobytes()
    audio_segment = AudioSegment(
        data=audio_bytes,
        sample_width=2,  # 16-bit audio
        frame_rate=sample_rate,
        channels=1
    )

    return audio_segment