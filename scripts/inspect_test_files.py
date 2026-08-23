import os
import sys
from pathlib import Path

def inspect_mp3(file_path):
    size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f:
        data = f.read()
    valid = data.startswith(b'ID3') or (len(data) > 4 and data[0] == 0xFF and (data[1] & 0xE0) == 0xE0)
    
    offset = 0
    if data.startswith(b'ID3'):
        tag_size = ((data[6] & 0x7F) << 21) | ((data[7] & 0x7F) << 14) | ((data[8] & 0x7F) << 7) | (data[9] & 0x7F)
        offset = 10 + tag_size
    
    frames = 0
    duration_sec = 0.0
    while offset < len(data) - 4:
        if data[offset] == 0xFF and (data[offset+1] & 0xE0) == 0xE0:
            version = (data[offset+1] >> 3) & 0x03
            layer = (data[offset+1] >> 1) & 0x03
            bitrate_idx = (data[offset+2] >> 4) & 0x0F
            sr_idx = (data[offset+2] >> 2) & 0x03
            padding = (data[offset+2] >> 1) & 0x01
            
            if version == 2 and layer == 1:
                bitrates = [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160, 0]
                srates = [22050, 24000, 16000, 0]
                br = bitrates[bitrate_idx] * 1000
                sr = srates[sr_idx]
                if br > 0 and sr > 0:
                    frame_size = int((576 * br / sr) / 8) + padding
                    frames += 1
                    duration_sec += 576.0 / sr
                    offset += max(frame_size, 1)
                    continue
            elif version == 3 and layer == 1:
                bitrates = [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 0]
                srates = [44100, 48000, 32000, 0]
                br = bitrates[bitrate_idx] * 1000
                sr = srates[sr_idx]
                if br > 0 and sr > 0:
                    frame_size = int((1152 * br / sr) / 8) + padding
                    frames += 1
                    duration_sec += 1152.0 / sr
                    offset += max(frame_size, 1)
                    continue
        offset += 1
    
    if duration_sec == 0:
        duration_sec = (size * 8) / 64000.0
        
    return size, duration_sec, valid

def main():
    test_dir = Path("test")
    files = sorted([f for f in test_dir.glob("*.mp3")])
    
    print("-" * 65)
    print(f"| {'Filename':<25} | {'Size (KB)':<10} | {'Duration':<12} | {'Valid':<6} |")
    print("-" * 65)
    
    for f in files:
        sz, dur, val = inspect_mp3(f)
        dur_str = f"{int(dur//60)}m {dur%60:.1f}s" if dur >= 60 else f"{dur:.1f}s"
        print(f"| {f.name:<25} | {sz/1024:<10.1f} | {dur_str:<12} | {str(val):<6} |")
    
    print("-" * 65)

if __name__ == "__main__":
    main()
