import argparse
import orjson
import requests
import cv2
import os
import numpy as np
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Download the data from a dataset json file.')
parser.add_argument('--dataset', type=str, default=None, required=True, help='The combined dataset json file.')
parser.add_argument('--dataset-downloaded', type=str, default=None, help='The combined dataset json file, including only the downloaded data.')
parser.add_argument('--folder', type=str, default=None, required=True, help='The folder to output the image data to.')
parser.add_argument('--image_width', type=int, default=512, help='The width of an output image.')
parser.add_argument('--image_height', type=int, default=512, help='The height of an output image.')
parser.add_argument('--replace', action="store_true", help='Replace existing images.')

opt = parser.parse_args()
print(opt)

############################################

def resize_image_without_distortion(img, width, height):
    # get image size
    h, w = img.shape[:2]

    # calculate aspect ratio
    aspect_ratio = w / h
    if h > w:
        new_h, new_w = height, int(height * aspect_ratio)
    else:
        new_w, new_h = width, int(width / aspect_ratio)

    img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)

    # calculate padding
    top_pad = (height - new_h) // 2
    bottom_pad = height - new_h - top_pad
    left_pad = (width - new_w) // 2
    right_pad = width - new_w - left_pad

    # pad the image and repeat the border
    padded_image = cv2.copyMakeBorder(img, top_pad, bottom_pad, left_pad, right_pad, cv2.BORDER_REPLICATE)

    return padded_image

def download(dataset):
    
    downloaded_dataset = []
    for item in tqdm(dataset):
        
        image_path = os.path.join(opt.folder, item['image'])

        # check if image already exists
        if not opt.replace and os.path.isfile(image_path):
            print(f'Image already exists: {item["image"]}. Skipping.')
            downloaded_dataset.append(item)
            continue

        # download image
        response = requests.get(item['url'])

        # check for status code
        if response.status_code != 200:
            print(f'Error downloading image: {item["url"]}. Skipping.')
            continue
    
        # check for content type
        if response.headers['content-type'].split('/')[0] != 'image':
            print(f'{item["url"]} is not an image. Skipping.')
            continue

        # load image
        img = np.asarray(bytearray(response.content), dtype=np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_UNCHANGED)

        # transform image
        img = resize_image_without_distortion(img, opt.image_width, opt.image_height)

        # create folder
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        cv2.imwrite(image_path, img)
        
        downloaded_dataset.append(item)

    return downloaded_dataset   

############################################

def main():

    dataset = []

    # load dataset and download data
    if os.path.isfile(opt.dataset):
        with open(opt.dataset, 'rb') as f:
            print(f'Loading dataset from file: {opt.dataset}')
            dataset = orjson.loads(f.read())
            print(f'Size dataset: {len(dataset)}')

            # download data
            dataset = download(dataset)

    if opt.dataset_downloaded:
        output_path = opt.dataset_downloaded
    else:
        output_path = opt.dataset

    # write dataset that has been downloaded
    with open(output_path, 'wb') as f:
        print(f'Writing data to file: {output_path}')
        f.write(orjson.dumps(dataset))

if __name__ == '__main__':
    main()