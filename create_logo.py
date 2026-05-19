import cv2
import numpy as np

# Create a 128x128 solid white background (Initialize with 255)
img = np.full((128, 128), 255, dtype=np.uint8)

# Draw a solid black circle (the baseball) (Color set to 0)
cv2.circle(img, (64, 64), 56, 0, -1)

# Draw the left and right stitches (thick white arcs) (Color set to 255)
cv2.ellipse(img, (16, 64), (40, 48), 0, -70, 70, 255, 8)
cv2.ellipse(img, (112, 64), (40, 48), 180, -70, 70, 255, 8)

cv2.imwrite('logo.png', img)
print("Success: 128x128 baseball logo.png created in your folder!")