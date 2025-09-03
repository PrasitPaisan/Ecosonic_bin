from pydub import AudioSegment
import os

def amplify_audio(input_file):
    # โหลดไฟล์เสียง
    audio = AudioSegment.from_file(input_file)
    
    # คำนวณ headroom = ระยะห่างจาก peak ของเสียงถึง 0 dBFS
    headroom  = 0.0 - audio.max_dBFS
    
    # เลือก gain ที่น้อยกว่าหรือเท่ากับ headroom (สูงสุด 10 dB)
    gain_dB = min(7, headroom)

    # เพิ่มเสียงโดยไม่เกิน headroom
    louder_audio = audio.apply_gain(gain_dB)

    output_path = './temp_output_amp.wav'
    louder_audio.export(output_path, format='wav')
    print(f"Audio amplified by {gain_dB} dB, saved to {output_path}")

    return output_path
