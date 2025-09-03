import librosa
import noisereduce as nr
import soundfile as sf

def reduce_audio_noise(
    input_path: str,
    sample_rate: int = 22050,
    prop_decrease: float = 0.3
):
 
    audio_data, sr = librosa.load(input_path, sr=sample_rate)

    noise_sample = audio_data[:sr]

    reduced_noise_audio = nr.reduce_noise(
        y=audio_data,
        sr=sr,
        y_noise=noise_sample,
        prop_decrease=prop_decrease
    )

    # Save output
    # sf.write(output_path, reduced_noise_audio, sr)
    print(f" ===> Finished noise reduction <===")

    return reduced_noise_audio, sr
