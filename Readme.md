# Ecosonic System

Ecosonic System is an audio-based classification pipeline that processes sound recordings, reduces noise, segments actions, converts audio to mel spectrogram images, and classifies them using a pre-trained VGG16 model.

## Project Structure

```
.
├── app.py
├── requirements.txt
├── models/
│   ├── VGG16_pre_ep100_01_.h5
│   └── VGG16_pre_ep100_01.txt
├── sensor/
│   ├── open_lib_control.py
│   ├── servo_control.py
│   └── stepper_control.py
├── service/
│   ├── converting_sound_to_mel_image.py
│   ├── cut_sound.py
│   └── redution.py
└── utils/
    ├── convert_to_byte.py
    ├── plot_compare.py
    └── preprocess_the_image.py
```

## Main Pipeline

The main script is [`app.py`](app.py), which performs the following steps:

1. **Load Audio**: Reads an input audio file.
2. **Noise Reduction**: Reduces noise using [`reduce_audio_noise`](service/redution.py).
3. **Convert to Bytes**: Converts the processed audio to 16-bit PCM using [`convert_to_2bytes`](utils/convert_to_byte.py).
4. **Plot Comparison**: Plots original vs. noise-reduced audio using [`plot_compare`](utils/plot_compare.py).
5. **Cut Sound**: Segments the audio into actions using [`cut_sound_per_action`](service/cut_sound.py).
6. **Convert to Mel Spectrogram**: Converts each segment to a mel spectrogram image using [`sound_to_image`](service/converting_sound_to_mel_image.py).
7. **Image Preprocessing**: Prepares images for prediction using [`convert_to_array`](utils/preprocess_the_image.py).
8. **Prediction**: Loads a pre-trained VGG16 model and predicts the class of each image.
9. **Cleanup**: Deletes temporary result folders.

## Requirements

Install dependencies with:

```sh
pip install -r requirements.txt
```

## Usage

1. Place your input audio file and update the `input_path` in [`app.py`](app.py).
2. Run the main script:

```sh
python app.py
```

## Hardware Control

- [`sensor/servo_control.py`](sensor/servo_control.py): Controls a servo motor via GPIO.
- [`sensor/stepper_control.py`](sensor/stepper_control.py): Controls stepper motors via GPIO.
- [`sensor/open_lib_control.py`](sensor/open_lib_control.py): Integrates IR sensor, LED, and servo for interactive control.

## Model

The classification model is a pre-trained VGG16 stored in [`models/VGG16_pre_ep100_01_.h5`](models/VGG16_pre_ep100_01_.h5).

## Notes

- This project is designed for use with a Raspberry Pi (GPIO control).
- Temporary files and folders are cleaned up automatically after prediction.

## License

This project is for educational