import glob
import os

from deta import Deta


images_path = r"F:\Data\FREE\WebP\x360\*.webp"


deta = Deta()

dd = deta.Drive("free_images")


def get_images():
	return glob.glob(images_path)

images = get_images()

for image in images:
    print(f"Upload: {os.path.basename(image)}")
    dd.put(name=os.path.basename(image), path=image)
