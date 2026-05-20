import cv2
import numpy as np
import matplotlib.pyplot as plt
import os

# Set Matplotlib to non-interactive mode
import matplotlib
matplotlib.use('Agg')

def create_comparison(img1, title1, img2, title2, output_path, cmap=None):
    plt.figure(figsize=(12, 6))
    plt.subplot(1, 2, 1)
    if cmap:
        plt.imshow(img1, cmap=cmap)
    else:
        plt.imshow(cv2.cvtColor(img1, cv2.COLOR_BGR2RGB))
    plt.title(title1, fontsize=14)
    plt.axis('off')

    plt.subplot(1, 2, 2)
    if cmap:
        plt.imshow(img2, cmap=cmap)
    else:
        plt.imshow(cv2.cvtColor(img2, cv2.COLOR_BGR2RGB))
    plt.title(title2, fontsize=14)
    plt.axis('off')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()

def generate_readme_assets():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(project_root, 'assets')
    result_dir = os.path.join(project_root, 'result')
    
    if not os.path.exists(assets_dir):
        os.makedirs(assets_dir)
    
    doc_out_dir = assets_dir

    img_path = os.path.join(assets_dir, 'test_image.jpg')
    logo_path = os.path.join(assets_dir, 'logo.png')
    
    if not os.path.exists(img_path) or not os.path.exists(logo_path):
        print(f"Error: Missing files in {assets_dir}")
        return

    from watermark_eval import prepare_image_watermark, embed_dct_unbreakable, extract_dct_unbreakable, calculate_accuracy

    original_bgr = cv2.imread(img_path)
    
    # --- 1. Logo Transformation ---
    logo_gray = cv2.imread(logo_path, cv2.IMREAD_GRAYSCALE)
    _, logo_bin_display = cv2.threshold(logo_gray, 127, 255, cv2.THRESH_BINARY)
    cv2.imwrite(os.path.join(doc_out_dir, 'readme_step1_logo.png'), logo_bin_display)

    # --- 2. Channel & Block Selection ---
    green_channel = original_bgr[:, :, 1]
    create_comparison(cv2.cvtColor(original_bgr, cv2.COLOR_BGR2RGB), "Original Image", green_channel, "Green Channel (Carrier)", 
                      os.path.join(doc_out_dir, 'readme_step2_carrier.png'), cmap='gray')

    # --- 3. DCT Frequency Domain (Enhanced 3-Panel Breakdown) ---
    # Use textured block at (1760, 2120) found via scan
    y, x = 1760, 2120
    sample_block = np.float32(green_channel[y:y+8, x:x+8])
    dct_block = cv2.dct(sample_block)
    reconstructed_block = cv2.idct(dct_block)
    
    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(18, 5))
    
    # Panel 1: Original Pixels
    ax1.imshow(sample_block, cmap='gray')
    ax1.set_title("1. Piksel Asli (8x8)", fontsize=14)
    for (j, i), label in np.ndenumerate(sample_block):
        ax1.text(i, j, int(label), ha='center', va='center', color='red', fontsize=7)
    
    # Panel 2: DCT Coefficients
    norm_dct = np.log(np.abs(dct_block) + 1)
    ax2.imshow(norm_dct, cmap='magma')
    ax2.set_title("2. Koefisien DCT", fontsize=14)
    for (j, i), label in np.ndenumerate(dct_block):
        ax2.text(i, j, f"{label:.0f}", ha='center', va='center', color='white', fontsize=7)

    # Panel 3: Reconstructed Pixels (IDCT)
    ax3.imshow(reconstructed_block, cmap='gray')
    ax3.set_title("3. Rekonstruksi (IDCT)", fontsize=14)
    for (j, i), label in np.ndenumerate(reconstructed_block):
        ax3.text(i, j, int(round(label)), ha='center', va='center', color='green', fontsize=7)

    plt.tight_layout()
    plt.savefig(os.path.join(doc_out_dir, 'readme_step3_breakdown.png'), dpi=150)
    plt.close()

    # DCT overview heatmap
    plt.figure(figsize=(6, 5))
    plt.imshow(np.log(np.abs(dct_block) + 1), cmap='magma')
    plt.title("DCT Frequency Coefficients\n(Low Freq at Top-Left)", fontsize=12)
    plt.colorbar()
    plt.savefig(os.path.join(doc_out_dir, 'readme_step3_dct.png'))
    plt.close()

    # --- 4. Watermark Embedding ---
    wm_binary, wm_h, wm_w = prepare_image_watermark(logo_path)
    watermarked_bgr = embed_dct_unbreakable(original_bgr, wm_binary, alpha=100, seed=42)
    create_comparison(original_bgr, "Before Watermarking", watermarked_bgr, "After Watermarking (Invisible)", 
                      os.path.join(doc_out_dir, 'readme_step4_comparison.png'))

    # --- 5. Difference Map ---
    diff = cv2.absdiff(original_bgr[:, :, 1], watermarked_bgr[:, :, 1])
    diff_viz = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX)
    cv2.imwrite(os.path.join(doc_out_dir, 'readme_step5_diff_map.png'), diff_viz)

    # --- 6. Robustness Test ---
    qf_cases = [50, 11, 10, 5]
    fig, axes = plt.subplots(2, 4, figsize=(20, 10))
    for i, q in enumerate(qf_cases):
        img_q_path = os.path.join(result_dir, f'image_qf{q}.jpg')
        if not os.path.exists(img_q_path):
            continue
        compressed_img = cv2.imread(img_q_path)
        extracted_wm = extract_dct_unbreakable(compressed_img, wm_h, wm_w, seed=42)
        acc = calculate_accuracy(wm_binary, extracted_wm)
        axes[0, i].imshow(cv2.cvtColor(compressed_img, cv2.COLOR_BGR2RGB))
        axes[0, i].set_title(f"Gambar Terkompresi (QF {q})", fontsize=16, fontweight='bold')
        axes[0, i].axis('off')
        axes[1, i].imshow(extracted_wm, cmap='gray')
        axes[1, i].set_title(f"Hasil Ekstraksi\nAccuracy: {acc:.1f}%", fontsize=14)
        axes[1, i].axis('off')
    plt.tight_layout()
    plt.savefig(os.path.join(doc_out_dir, 'readme_robustness_comparison.png'), dpi=150)
    plt.close()

    print(f"README assets generated in: {doc_out_dir}")

if __name__ == "__main__":
    generate_readme_assets()
