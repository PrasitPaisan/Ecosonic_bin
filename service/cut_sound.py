from pydub import AudioSegment
from pydub.silence import detect_nonsilent 
import os 

# def cut_sound_per_action(input_path, output_dir, sample_rate, action_duration=400, length_duration=700):
#     print("Cutting sound per action . . . ")
#     # Ensure output directory exists
#     os.makedirs(output_dir, exist_ok=True)
    
#     sound = AudioSegment.from_wav(input_path)
#     nonsilent_ranges = detect_nonsilent(sound, min_silence_len=action_duration, silence_thresh=-35)

#     if not nonsilent_ranges:
#         print("No sound detection in this file")
#         return False
    
#     for i, (start, end) in enumerate(nonsilent_ranges):
#         segment = sound[start:end]
#         if len(segment) < length_duration:
#             silence_to_add = AudioSegment.silent(duration=length_duration - len(segment))
#             segment += silence_to_add

#         segment = segment[:length_duration] 

#         output_file = f"{output_dir}/value_{i + 1}.wav"
#         segment.export(output_file, format="wav")  
#     print(f"Finished cutting sound per action , {len(nonsilent_ranges)} actions")     
#     return True


def cut_sound_per_action(input_path, output_dir, sample_rate=None,
                         action_duration=500, length_duration=700,
                         silence_thresh=-35, frame_ms=5):
    """
    Cut sound into segments:
    - ใช้ detect_nonsilent() เหมือนเดิม
    - แต่เลื่อนจุดเริ่ม (start) ไปที่มิลลิวินาทีแรกที่เสียงดังเกิน silence_thresh (-35 dBFS)
    - เติม silence ถ้าสั้นกว่า length_duration และตัดให้ครบ
    """

    print("Cutting sound per action . . .")

    os.makedirs(output_dir, exist_ok=True)
    sound = AudioSegment.from_file(input_path)

    # ตรวจหา non-silent ช่วงต่าง ๆ
    nonsilent_ranges = detect_nonsilent(
        sound,
        min_silence_len=action_duration,
        silence_thresh=silence_thresh,
        seek_step=1
    )

    if not nonsilent_ranges:
        print("No sound detection in this file")
        return False

    # ===== helper หา "มิลลิวินาทีแรกที่เสียงดังเกิน thresh" =====
    def first_crossing_ms(seg: AudioSegment, start_ms: int, end_ms: int,
                          thresh_db: float, hop_ms: int) -> int:
        limit = min(end_ms, max(0, len(seg) - hop_ms))
        t = max(0, start_ms)
        while t <= limit:
            chunk = seg[t:t + hop_ms]
            db = chunk.dBFS
            if db != float('-inf') and db > thresh_db:
                return t
            t += 1  # เดินละเอียดทีละ 1 ms
        return start_ms

    # ===== ตัดไฟล์ตามช่วงที่ตรวจเจอ =====
    for i, (start, end) in enumerate(nonsilent_ranges):
        # เลื่อน start ไปยังจุดที่ดังเกิน -35 dBFS ครั้งแรก
        strict_start = first_crossing_ms(sound, start, end, silence_thresh, frame_ms)

        segment = sound[strict_start:end]

        # ถ้าสั้น เติม silence
        if len(segment) < length_duration:
            silence_to_add = AudioSegment.silent(duration=length_duration - len(segment))
            segment += silence_to_add

        # บังคับความยาว 1000 ms
        segment = segment[:length_duration]

        output_file = f"{output_dir}/value_{i + 1}.wav"
        segment.export(output_file, format="wav")
        print(f"Exported: {output_file}")

    print(f"Finished cutting sound per action , {len(nonsilent_ranges)} actions")
    return True
