import cv2
import numpy as np
import os
import sys

# Add 'main' to sys.path
sys.path.append(os.path.join(os.getcwd(), 'main'))

from watermark_eval import prepare_image_watermark, embed_dct_unbreakable, extract_dct_unbreakable, calculate_accuracy

def analyze_low_qf():
    assets_dir = 'assets'
    temp_dir = 'result'
    logo_path = os.path.join(assets_dir, 'logo.png')
    img_path = os.path.join(assets_dir, 'test_image.jpg')
    
    if not os.path.exists(img_path) or not os.path.exists(logo_path):
        print("Missing assets.")
        return

    original_img = cv2.imread(img_path)
    wm_binary, wm_h, wm_w = prepare_image_watermark(logo_path)
    
    print("Embedding Watermark (Alpha=100)...")
    watermarked_img = embed_dct_unbreakable(original_img, wm_binary, alpha=100, seed=42)
    
    print("\nAccuracy Analysis for QF 1 to 20:")
    print("-" * 30)
    
    for q in range(20, 0, -1):
        temp_out = os.path.join(temp_dir, f'temp_low_qf{q}.jpg')
        cv2.imwrite(temp_out, watermarked_img, [int(cv2.IMWRITE_JPEG_QUALITY), q])
        
        compressed = cv2.imread(temp_out)
        extracted = extract_dct_unbreakable(compressed, wm_h, wm_w, seed=42)
        acc = calculate_accuracy(wm_binary, extracted)
        
        print(f"QF {q:2}: {acc:6.2f}%")
        
        if os.path.exists(temp_out):
            os.remove(temp_out)

if __name__ == "__main__":
    analyze_low_qf()
