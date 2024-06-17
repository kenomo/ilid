import argparse
import orjson
import hashlib
from tqdm import tqdm
import re

parser = argparse.ArgumentParser(description='Preprocess the data from one store.')
parser.add_argument('--file', type=str, default=None, help='The json file to process.')
parser.add_argument('--output', type=str, default=None, help='The file to output the json data to.')
parser.add_argument('--regex', type=str, default=None, help='Additional regex to filter the data.')

opt = parser.parse_args()
print(opt)

############################################

def filter_duplicate_urls(data):
    unique_urls = {}
    for item in tqdm(data):
        url_hash = hashlib.md5(item['url'].encode('utf-8')).hexdigest()
        if url_hash not in unique_urls:
            unique_urls[url_hash] = item
    unique_data = list(unique_urls.values())
    return unique_data

def remove_empty_labels(data):
    return [item for item in tqdm(data) if item['web']['label']]

def remove_empty_data(data):
    for item in tqdm(data):
        item['web']['data'] = [d for d in item['web']['data'] if d]
    data = [item for item in data if item['web']['data']]
    return data

def remove_escape_sequences(data):
    for item in tqdm(data):
        item['web']['label'] = item['web']['label'].replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
        for i in range(len(item['web']['data'])):
            item['web']['data'][i] = item['web']['data'][i].replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()
    return data

def regex_filter(data):
    if opt.regex is not None:
        for item in tqdm(data):
            item['web']['label'] = re.sub(opt.regex, "", item['web']['label'], flags=re.IGNORECASE)
            item['web']['data'] = [re.sub(opt.regex, "", d, flags=re.IGNORECASE) for d in item['web']['data']]
    return data

def remove_numbers(data):
    for item in tqdm(data):
        item['web']['label'] = re.sub(r"\d+", "", item['web']['label'])
        item['web']['data'] = [re.sub(r"\d+", "", d) for d in item['web']['data']]
    return data

############################################

def main():

    data = None

    with open(opt.file, 'rb') as f:
        print(f'Loading data from file: {opt.file}')
        data = orjson.loads(f.read())
        print(f'Size: {len(data)}')
        
        print(f'Filtering duplicate URLs...')
        data = filter_duplicate_urls(data)
        print(f'Size: {len(data)}')

        print(f'Filtering empty labels...')
        data = remove_empty_labels(data)
        print(f'Size: {len(data)}')

        print(f'Filtering empty data...')
        data = remove_empty_data(data)
        print(f'Size: {len(data)}')

        print(f'Filtering escape sequences...')
        data = remove_escape_sequences(data)
        print(f'Size: {len(data)}')

        print(f'Applying regex filter...')
        data = regex_filter(data)
        print(f'Size: {len(data)}')

        print(f'Removing numbers...')
        data = remove_numbers(data)
        print(f'Size: {len(data)}')

    with open(opt.output, 'wb') as f:
        print(f'Writing data to file: {opt.output}')
        f.write(orjson.dumps(data))

if __name__ == '__main__':
    main()