import argparse
import orjson
import os
from tqdm import tqdm
import uuid

parser = argparse.ArgumentParser(description='Add the data from one store to a combined dataset json file.')
parser.add_argument('--file', type=str, default=None, required=True, help='The json file to process.')
parser.add_argument('--dataset', type=str, default=None, required=True, help='The combined dataset json file.')
parser.add_argument('--source_tag', type=str, default=None, required=True, help='The source tag.')

opt = parser.parse_args()
print(opt)

############################################

def assemble(data, dataset):
    
    for item in tqdm(data):
        
        # prevent adding the same URL
        for d in dataset:
            if d['url'] == item['url']:
                print(f'URL already exists: {item["url"]}. Skipping.')
                continue
        
        id = str(uuid.uuid4())
        relative_path = os.path.join(item['folder_name'], id + '.png')

        # add to dataset
        dataset.append({
            'id': id,
            'image': relative_path,
            'url': item['url'],
            'label_short': item['label_short'],
            'label_long': item['label_long'],
            'description': item['description'],
            'material': item['material'],
            'material_finish': item['material_finish'],
            'source': opt.source_tag
        })

    return dataset   

############################################

def main():

    data = None
    dataset = []

    # load combined dataset
    if os.path.isfile(opt.dataset):
        with open(opt.dataset, 'rb') as f:
            print(f'Loading dataset from file: {opt.dataset}')
            dataset = orjson.loads(f.read())
            print(f'Size dataset: {len(dataset)}')

    # process data to add
    with open(opt.file, 'rb') as f:
        print(f'Loading data from file: {opt.file}')
        data = orjson.loads(f.read())
        print(f'Size processed data: {len(data)}')
        
        print(f'Assemble data')
        dataset = assemble(data, dataset)

        print(f'Size dataset: {len(dataset)}')

    # write combined dataset
    with open(opt.dataset, 'wb') as f:
        print(f'Writing data to file: {opt.dataset}')
        f.write(orjson.dumps(dataset))

if __name__ == '__main__':
    main()