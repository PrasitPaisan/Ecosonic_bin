import numpy as np 
import matplotlib.pyplot as plt


def plot_compare(original_audio, reduced_audio, sample_rate):
    
    time = np.linspace(0, len(original_audio) / sample_rate, num=len(original_audio))
    plt.figure(figsize=(12, 5))
    plt.plot(time, original_audio, label="Original", alpha=0.7, color='blue')
    plt.plot(time, reduced_audio, label="Noise Reduced", alpha=0.7, color='red')
    plt.title("Original vs Noise Reduced Audio")
    plt.xlabel("Time (s)")
    plt.ylabel("Amplitude")
    plt.legend()
    plt.grid()
    plt.tight_layout()
    plt.show()