import os
import pathlib
import shutil
import urllib.request
from PIL import Image

from lovedjeans.settings import BASE_DIR
from .tools import IMAGES_URL


def save_images(images, sku, title):
    image_folder = os.path.join(BASE_DIR, pathlib.Path("staticfiles/media/product-images"), sku)
    urls = []
    try:
        os.mkdir(image_folder)
    except FileExistsError:
        pass
    image_files = [None] * 12
    for key,value in images.items():
        image_files[int(key[4])] = value
    for i,image in enumerate(image_files):
        if not image:
            continue
        fixed_title = title.replace(" ", "-")
        img = Image.open(image)
        img_save_location = os.path.join(image_folder, f"{fixed_title}_{i}.jpg")
        img.save(img_save_location)
        urls.append((IMAGES_URL + sku + f"/{fixed_title}_{i}.jpg").replace("'",'"'))
    return urls

def download_images(urls, sku, title):
    image_folder = os.path.join(BASE_DIR, pathlib.Path("staticfiles/media/product-images"), sku)
    try:
        os.mkdir(image_folder)
    except FileExistsError:
        pass
    for i,url in enumerate(urls):
        fixed_title = title.replace(" ", "-")
        image = urllib.request.urlopen(url)
        image = Image.open(image)
        save_location = os.path.join(image_folder, f"{fixed_title}_{i}.jpg")
        image.save(save_location)
    return urls

def delete_folder(path):
    abs_path = os.path.realpath(path)
    allowed_base = os.path.realpath("staticfiles/media/product-images")
    if not abs_path.startswith(allowed_base + os.sep):
        raise ValueError(f"Refusing to delete path outside media directory: {abs_path}")
    shutil.rmtree(abs_path, ignore_errors=True)

def get_images(sku):
    image_folder = os.path.join(BASE_DIR, pathlib.Path("static_files/media/product-images"), sku)
    images = []
    for image in os.listdir(image_folder):
        images.append(f"{IMAGES_URL}{sku}/{image}")
    return ";".join(images)
