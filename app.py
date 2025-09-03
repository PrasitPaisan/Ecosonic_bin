import librosa
import shutil
import os
from PIL import Image
from tensorflow.keras.models import load_model
import sounddevice as sd
from scipy.io.wavfile import write
import time

from service.redution import reduce_audio_noise
from service.cut_sound import cut_sound_per_action
from utils.plot_compare import plot_compare
from utils.convert_to_byte import convert_to_2bytes
from service.converting_sound_to_mel_image import sound_to_image
from utils.preprocess_the_image import convert_to_array
from sensor.servo_control import set_angle,cleanup
from sensor.stepper_controls import setup_gpio, motor_control, reset_motors_position
from sensor.IR_sensor import read_ir_sensor
from service.amplify import amplify_audio   

Image.MAX_IMAGE_PIXELS = None

if __name__ == "__main__":
    try:
        class_names = ['battery', 'bottle', 'box', 'can', 'glass', 'paper', 'pingpong']
        model = load_model("./models/VGG-lite_01.h5")
        sample_rate = 22050
        duration = 3 # sec

        setup_gpio()
        print("System is ready, waiting for IR sensor trigger...")

        while True:
            if read_ir_sensor() == 0:

                print(f"Recording for {duration} seconds...")
                recording = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype='float32')
                sd.wait()
                print("Recording complete!")
                input_path = "temp_input.wav"

                start_time = time.time()

                write(input_path, sample_rate, recording) 

                # original_audio, sr = librosa.load(input_path, sr=sample_rate)
                # reduced_audio, _sr = reduce_audio_noise(input_path, sample_rate)

                amplified_path = amplify_audio(input_path) 

                # plot_compare(original_audio=original_audio, reduced_audio=amplified_sound, sample_rate=sr)

                check_action = cut_sound_per_action(amplified_path, "./results/sound", sample_rate)


                if not check_action:
                    print("No actions detected, skipping processing.")
                    continue

                sound_to_image(dataset_path="./results/sound", output_path="./images", n_mels=256, n_fft=2048, hop_length=256)

                # Predict the image
                class_predicted = []
                for dirpath, dirnames, filenames in os.walk("./images"):
                    for f in filenames:
                        if f.endswith('.png'):
                            img_path = os.path.join(dirpath, f)
                            img_array = convert_to_array(img_path)
                            pred = model.predict(img_array)
                            predicted_class_index = pred.argmax(axis=1)[0]
                            class_predicted.append(predicted_class_index)
                
                
                if class_predicted:
                    for i in range(len(class_predicted)):
                        print(f"Rotating motor for class: {class_names[class_predicted[i]]} : {class_predicted[i]}")
                    motor_control(int(class_predicted[0]))
                    time.sleep(0.2)
                    set_angle(120)
                    time.sleep(2)
                    set_angle(0)
                else:
                    print("No valid class predicted, no motor rotation.")

                # Detete the results after finish prediction
                shutil.rmtree('./results')
                shutil.rmtree("./images")
                os.remove(amplified_path)
                os.remove(input_path)

                end_time = time.time() 
                print(f"Processing time: {end_time - start_time:.2f} seconds")

    except KeyboardInterrupt:
        print("Exiting program")
        reset_motors_position()
        cleanup()