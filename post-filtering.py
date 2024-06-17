import argparse
import orjson
from tqdm import tqdm
import re

parser = argparse.ArgumentParser(description='Postprocessing the data from one store.')
parser.add_argument('--file', type=str, default=None, help='The json file to process.')
parser.add_argument('--output', type=str, default=None, help='The file to output the json data to.')
parser.add_argument('--min_field_length', type=int, default=4, help='The minimum length of a field.')

opt = parser.parse_args()
print(opt)

############################################

def clean_field(field, r="[^\d\w\s\-_\.]"):
    field = re.sub(r, '', field)
    field = field.strip()
    if len(field) < opt.min_field_length:
        return None
    return field

def clean_fields(data):

    new_data = []

    # apply cleaning to all fields and lower the label
    for item in tqdm(data):

        # check if fields are present
        if not "label_short" in item:
            continue
        if not "label_long" in item:
            continue
        
        # check if fields are not empty
        if item['label_short'] is None:
            continue
        if item['label_long'] is None:
            continue

        # clean fields
        item['label_short'] = clean_field(item['label_short']).lower()
        item['label_long'] = clean_field(item['label_long']).lower()
        
        if item['label_short'] is None:
            continue
        if item['label_long'] is None:
            continue

        if item['description']:
            item['description'] = clean_field(item['description'])

        if item['material']:
            item['material'] = clean_field(item['material'])
        if item['material']:
            item['material'] = item['material'].lower()

        if item['material_finish']:
            item['material_finish'] = clean_field(item['material_finish'])
        if item['material_finish']:
            item['material_finish'] = item['material_finish'].lower()
        
        new_data.append(item)

    return new_data

def generate_folder_names(data):
    for item in tqdm(data):
        label_short_total_cleaned = clean_field(item['label_short'], r="[^\d\w\s\-_]")
        item['folder_name'] = '_'.join(label_short_total_cleaned.split())
    return data

############################################

def main():

    data = None

    with open(opt.file, 'rb') as f:
        print(f'Loading data from file: {opt.file}')
        data = orjson.loads(f.read())
        print(f'Size: {len(data)}')
        
        print(f'Cleaning fields...')
        data = clean_fields(data)
        print(f'Size: {len(data)}')

        print(f'Generate folder names...')
        data = generate_folder_names(data)

    with open(opt.output, 'wb') as f:
        print(f'Writing data to file: {opt.output}')
        f.write(orjson.dumps(data))

if __name__ == '__main__':
    main()