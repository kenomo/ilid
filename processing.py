import argparse
import orjson
from transformers import AutoTokenizer, AutoModelForCausalLM
from huggingface_hub import login
import torch
from linetimer import CodeTimer
from random import random
import re
from tqdm import tqdm

parser = argparse.ArgumentParser(description='Processing the data from one source.')
parser.add_argument('--file', type=str, default=None, help='The json file to process.')
parser.add_argument('--output', type=str, default=None, help='The file to output the json data to.')
parser.add_argument('--model', type=str, default="meta-llama/Meta-Llama-3-8B-Instruct", help='Model to use.')
parser.add_argument('--access_token', type=str, default=None, help='Huggingface access token.')
parser.add_argument('--silent', type=bool, default=True, help='Surpress linetimer messages.')
parser.add_argument('--debug', type=float, default=0, help='If set large than 0, only --debug percentage will be randomly processed.')

opt = parser.parse_args()
print(opt)

############################################

def generate(data, tokenizer, model):
    # get device
    device = model.device
    
    for item in tqdm(data):

        # debug mode
        if opt.debug > 0.0:
            if random() > opt.debug:
                continue
        
        # get data from item
        web_label = item['web']['label']
        web_data = ", ".join(item['web']['data'])

        # define messages
        messages = [
            {
                "role": "system", 
                "content": "" + \
                    "You are a helpful assistant for a company that sells industrial products.\n" + \
                    "Do not ask for further details or state additional questions.\n" + \
                    "Do not add additional information or details that are not given by the user."
            },
            {
                "role": "user", 
                "content": "" + \
                    "Summarize " + \
                    "'" + \
                    "Label: " + web_label + "\n" + \
                    "Text: " + web_data + \
                    "'\n" + \
                    "returning the following information: \n" + \
                    "(1) a long label or name of the product without ids, numbers, codes, or sizes " + \
                    "(2) a short label or name of the product with a maximum of 4 words and shorter than the long label " + \
                    "(3) description of the product with a maximum of 30 words without ids, numbers, codes, or sizes " + \
                    "(4) material with a maximum of 5 words " + \
                    "(5) material finish/color with a maximum of 5 words"
            },
        ]

        # tokenize prompt
        # https://huggingface.co/docs/transformers/main_classes/tokenizer#transformers.PreTrainedTokenizer
        inputs = tokenizer.apply_chat_template(
            messages,
            add_generation_prompt=True,
            return_tensors="pt"
        ).to(device)

        # generate response
        # https://huggingface.co/docs/transformers/main_classes/text_generation#transformers.GenerationConfig
        # do_sample (bool, optional, defaults to False) — Whether or not to use sampling ; use greedy decoding otherwise.
        # top_p (float, optional, defaults to 1.0) — If set to float < 1, only the smallest set of most probable tokens with probabilities that add up to top_p or higher are kept for generation.
        # top_k (int, optional, defaults to 50) — If set to int > 0, only the top k tokens with the highest probability in the distribution are considered for generation.
        # max_new_tokens (int, optional) — The maximum numbers of tokens to generate, ignoring the number of tokens in the prompt.
        # use_cache (bool, optional, defaults to True) — Whether or not the model should use the past last key/values attentions (if applicable to the model) to speed up decoding.
        with CodeTimer("Generation", silent=opt.silent):
            outputs = model.generate(
                inputs,
                do_sample=True,
                top_p=0.9,
                #top_k=100,
                temperature=0.6,
                max_new_tokens=256,
                eos_token_id=[
                    tokenizer.eos_token_id,
                    tokenizer.convert_tokens_to_ids("<|eot_id|>")
                ],
                pad_token_id=tokenizer.eos_token_id,
                #use_cache=False
            )

        # decode response
        # https://huggingface.co/docs/transformers/v4.38.2/en/main_classes/tokenizer#transformers.PreTrainedTokenizer.decode
        # skip_special_tokens (bool, optional, defaults to False) — Whether or not to remove special tokens in the decoding.
        response = tokenizer.decode(
            outputs[0][inputs.shape[-1]:], 
            skip_special_tokens=True
        )

        # post process response and extract information
        label_short = None
        label_long = None
        description = None
        material = None
        material_finish = None


        # finds and removes the (x) : ... pattern from the response
        def find_remove_pattern(r, d, s):
            pattern = lambda d, s: f"(((\({d}\)|{d}\.).*({s}).*:\s))|(\({d}\)|{d}\.)|(.*({s}).*:\s)"
            m = re.search(pattern(d, s), str(r), re.IGNORECASE)
            if m is not None:
                return r.replace(m.group(0), "").strip()
            return None
        
        # detect if model states none, not, ...
        def detect_none(s, p):
            m = re.search(f'({p})', str(s), re.IGNORECASE)
            if m is not None:
                return None
            return s
        
        # split response into list
        response = response.split("\n")
        
        # loop through lines
        for _, r in enumerate(response):

            # strip, remove dots
            r = r.strip()
            r = r.rstrip(".")

            # extract information
            if label_long is None:
                label_long = find_remove_pattern(r, "1", "label|name")
            elif label_short is None:
                label_short = find_remove_pattern(r, "2", "label|name")

            if description is None:
                description = find_remove_pattern(r, "3", "description")
            
            if material is None:
                material = find_remove_pattern(r, "4", "material")
                if material is not None:
                    material = detect_none(material, "none|not|N\/A|without|unknown")

            if material_finish is None:
                material_finish = find_remove_pattern(r, "5", "finish|color")
                if material_finish is not None:
                    material_finish = detect_none(material_finish, "none|not|N\/A|without|unknown")

        # check if we at least have a label
        label_short = detect_none(label_short, "none|not|N\/A|unknown")
        label_long = detect_none(label_long, "none|not|N\/A|unknown")

        # assign information to item
        item['response'] = response
        item['label_short'] = label_short
        item['label_long'] = label_long
        item['description'] = description
        item['material'] = material
        item['material_finish'] = material_finish

        del inputs, outputs, response

    return data

############################################

def main():

    data = None
    device = "cuda" if torch.cuda.is_available() else "cpu"

    login(token=opt.access_token)
    tokenizer = AutoTokenizer.from_pretrained(opt.model)
    model = AutoModelForCausalLM.from_pretrained(
        opt.model,
        torch_dtype="auto",
        device_map=device
    )
    model = torch.compile(model)

    with open(opt.file, 'rb') as f:
        print(f'Loading data from file: {opt.file}')
        data = orjson.loads(f.read())
        print(f'Size: {len(data)}')
        
        print(f'Generating labels, descriptions, ...')
        data = generate(data, tokenizer, model)
        print(f'Size: {len(data)}')

    with open(opt.output, 'wb') as f:
        print(f'Writing data to file: {opt.output}')
        f.write(orjson.dumps(data))

if __name__ == '__main__':
    main()