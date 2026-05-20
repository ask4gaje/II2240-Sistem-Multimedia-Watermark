import cv2
import numpy as np
import os

def find_textured_block():
    img_path = 'assets/test_image.jpg'
    if not os.path.exists(img_path):
        print("Missing asset")
        return

    img = cv2.imread(img_path)
    green = img[:, :, 1]
    h, w = green.shape
    
    max_var = -1
    best_coords = (0, 0)
    
    # Scan middle area of the image for texture
    for y in range(h // 4, 3 * h // 4, 8):
        for x in range(w // 4, 3 * w // 4, 8):
            block = green[y:y+8, x:x+8]
            var = np.var(block)
            if var > max_var:
                max_var = var
                best_coords = (y, x)
                
    print(f"Best: {best_coords} (Var: {max_var:.2f})")

if __name__ == "__main__":
    find_textured_block()
