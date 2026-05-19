import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

def prepare_image_watermark(logo_path):
    """Loads the logo and converts to strict B&W using its ORIGINAL resolution."""
    logo = cv2.imread(logo_path, cv2.IMREAD_GRAYSCALE)
    if logo is None:
        print(f"Error: Could not load '{logo_path}'.")
        exit()

    _, logo_binary = cv2.threshold(logo, 127, 1, cv2.THRESH_BINARY)
    wm_h, wm_w = logo_binary.shape
    return logo_binary, wm_h, wm_w

def get_shuffled_coordinates(h, w, seed=42):
    """Creates a randomized list of all 8x8 block coordinates."""
    coords = []
    for i in range(0, h, 8):
        for j in range(0, w, 8):
            coords.append((i, j))
            
    np.random.seed(seed)
    np.random.shuffle(coords)
    return coords

def embed_dct_unbreakable(image, watermark_binary, alpha=100, seed=42):
    """Embeds bits into Low-Mid frequencies scattered across the Green channel."""
    watermarked = image.copy()
    channel = np.float32(watermarked[:, :, 1]) # Green Channel
        
    h, w = channel.shape
    h -= h % 8
    w -= w % 8
    
    coords = get_shuffled_coordinates(h, w, seed)
    wm_h, wm_w = watermark_binary.shape
    redundancy = 3 # 3x redundancy for the 16MP photo
    
    # Capacity Safety Check
    max_blocks = len(coords)
    required_blocks = wm_h * wm_w * redundancy
    if required_blocks > max_blocks:
        print(f"\n--- CAPACITY ERROR ---")
        print(f"Host image blocks: {max_blocks} | Blocks needed: {required_blocks}")
        exit()
    
    coord_idx = 0
    
    for i in range(wm_h):
        for j in range(wm_w):
            wm_bit = watermark_binary[i, j]
            
            for _ in range(redundancy):
                y, x = coords[coord_idx]
                coord_idx += 1
                
                block = channel[y:y+8, x:x+8]
                dct_block = cv2.dct(block)
                
                # UNBREAKABLE TARGETS RESTORED: Low-Mid Frequencies
                c1, c2 = dct_block[2, 1], dct_block[1, 2]
                
                if wm_bit == 1:
                    if c1 <= c2 + alpha:
                        diff = (c2 + alpha - c1) / 2.0 + 1
                        dct_block[2, 1] += diff
                        dct_block[1, 2] -= diff
                else:
                    if c2 <= c1 + alpha:
                        diff = (c1 + alpha - c2) / 2.0 + 1
                        dct_block[1, 2] += diff
                        dct_block[2, 1] -= diff
                        
                channel[y:y+8, x:x+8] = cv2.idct(dct_block)
            
    channel = np.clip(channel, 0, 255).astype(np.uint8)
    watermarked[:h, :w, 1] = channel[:h, :w]
        
    return watermarked

def extract_dct_unbreakable(image, wm_h, wm_w, seed=42):
    """Extracts scattered bits from Low-Mid frequencies using Majority Voting."""
    channel = np.float32(image[:, :, 1])
        
    h, w = channel.shape
    h -= h % 8
    w -= w % 8
    
    extracted = np.zeros((wm_h, wm_w), dtype=np.uint8)
    coords = get_shuffled_coordinates(h, w, seed)
    coord_idx = 0
    redundancy = 3
    
    for i in range(wm_h):
        for j in range(wm_w):
            votes_for_one = 0
            
            for _ in range(redundancy):
                y, x = coords[coord_idx]
                coord_idx += 1
                
                block = channel[y:y+8, x:x+8]
                dct_block = cv2.dct(block)
                
                # UNBREAKABLE TARGETS RESTORED
                c1, c2 = dct_block[2, 1], dct_block[1, 2]
                
                if c1 > c2:
                    votes_for_one += 1
                    
            if votes_for_one >= 2:
                extracted[i, j] = 1
            else:
                extracted[i, j] = 0
                
    return extracted * 255

def calculate_accuracy(original_watermark, extracted_watermark):
    extracted_binary = (extracted_watermark > 127).astype(np.uint8)
    matches = np.sum(original_watermark == extracted_binary)
    return (matches / original_watermark.size) * 100

def main():
    img_path = 'test_image.jpg'
    logo_path = 'logo.png' 
    
    if not os.path.exists(img_path):
        print(f"Error: Could not find {img_path}")
        return
        
    original_img = cv2.imread(img_path)
    
    # Dynamic Size Extraction
    watermark_binary, wm_h, wm_w = prepare_image_watermark(logo_path)
    
    print("Embedding Watermark... (Targeting Low-Mid Frequencies, Alpha=100)")
    watermarked_img = embed_dct_unbreakable(original_img, watermark_binary, alpha=100, seed=42)

    # UPDATED: Changed to 8 distinct QF values to display
    qf_values = [100, 90, 75, 50, 20, 11, 8, 5] 
    
    # Changed to 12x12 so vertical stacked plots aren't squished
    plt.figure(figsize=(12, 12))
    plt.suptitle("File Size and Watermark (128x128) Accuracy", fontsize=18)

    for i, qf in enumerate(qf_values):
        temp_filename = f'temp_unbreakable_qf{qf}.jpg'
        
        # Save the file to disk
        cv2.imwrite(temp_filename, watermarked_img, [int(cv2.IMWRITE_JPEG_QUALITY), qf])
        
        # GET FILE SIZE IN KILOBYTES
        file_size_kb = os.path.getsize(temp_filename) / 1024.0
        
        # Read it back and extract
        compressed_img = cv2.imread(temp_filename)
        extracted_wm = extract_dct_unbreakable(compressed_img, wm_h, wm_w, seed=42)
        
        accuracy = calculate_accuracy(watermark_binary, extracted_wm)
        compressed_rgb = cv2.cvtColor(compressed_img, cv2.COLOR_BGR2RGB)
        
        # Calculate matrix mapping for a 4x4 plot grid (4 items top row group, 4 items bottom)
        col = i % 4
        row_group = i // 4  # 0 for first four QFs, 1 for last four QFs
        
        img_subplot_idx = (row_group * 2) * 4 + col + 1
        wm_subplot_idx = (row_group * 2 + 1) * 4 + col + 1
        
        # Plot Image with File Size Title
        plt.subplot(4, 4, img_subplot_idx)
        plt.imshow(compressed_rgb, interpolation='nearest') 
        plt.title(f"QF: {qf}\nSize: {file_size_kb:.1f} KB", fontsize=11, fontweight='bold')
        plt.axis('off')
        
        # Plot Extracted Logo
        plt.subplot(4, 4, wm_subplot_idx)
        plt.imshow(extracted_wm, cmap='gray', interpolation='nearest')
        plt.title(f"Accuracy: {accuracy:.1f}%", fontsize=11)
        plt.axis('off')
        
        if os.path.exists(temp_filename):
            os.remove(temp_filename)

    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()