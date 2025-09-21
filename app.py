import librosa
import shutil
import os
from PIL import Image
from tensorflow.keras.models import load_model
import sounddevice as sd
from scipy.io.wavfile import write
import time

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

def process_and_predict(model, class_names, amplified_path, input_path, sample_rate):
    check_action = cut_sound_per_action(amplified_path, "./results/sound", sample_rate)
    if not check_action:
        print("No actions detected, skipping processing.")
        safe_remove(amplified_path)
        safe_remove(input_path)
        time.sleep(0.2)
        return None

    sound_to_image_mel_mfcc(
        dataset_path="./results/sound",
        output_path="./images",
        n_mels=128, n_mfcc=20, n_fft=2048, hop_length=512
    )

    all_preds = []
    for dirpath, _, filenames in os.walk("./images"):
        for f in filenames:
            if f.endswith('.png'):
                img_path = os.path.join(dirpath, f)
                img_array = convert_to_array(img_path)
                pred = model.predict(img_array, verbose=0)
                predicted_class_index = pred.argmax(axis=1)[0]
                pred_max = float(pred.max())
                all_preds.append((predicted_class_index, pred_max))

    if all_preds:
        print("Class predictions and confidences:")
        for idx, (class_idx, confidence) in enumerate(all_preds):
            print(f"Image {idx+1}: {class_names[class_idx]} (class {class_idx}), confidence: {confidence*100:.2f}%")
        best_idx, best_conf = max(all_preds, key=lambda x: x[1])
        print(f"Best class: {class_names[best_idx]} (class {best_idx}), confidence: {best_conf*100:.2f}%")
        return best_idx
    else:
        print("No valid class predicted, no motor rotation.")
        return None

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
    try:
        LED_status_color("Red")
        class_names = ['battery', 'bottle', 'box', 'can', 'glass', 'paper', 'pingpong']
        model_name = "Resnet34_Mel_MFCC_1SEC_100each_noise70%_Rescaling_max_07SEC400-40.h5"
        model = load_model(f"./models/{model_name}")

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

                best_idx = process_and_predict(model, class_names, amplified_path, input_path, sample_rate)
                if best_idx is not None:
                    motor_control(int(best_idx))
                    time.sleep(0.2)
                    set_angle(120)
                    time.sleep(1)
                    set_angle(0)

                cleanup_artifacts(amplified_path, input_path)
                end_time = time.time()
                print(f"Processing time: {end_time - start_time:.2f} seconds")

            time.sleep(0.001)

    except KeyboardInterrupt:
        print("Exiting program")
        reset_motors_position()
        cleanup()
    finally:
        if detector is not None:
            detector.close
