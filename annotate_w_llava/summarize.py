import argparse
import torch
import os
import json
from tqdm import tqdm
import shortuuid

from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN
from llava.conversation import conv_templates, SeparatorStyle
from llava.model.builder import load_pretrained_model
from llava.utils import disable_torch_init
from llava.mm_utils import tokenizer_image_token, get_model_name_from_path, KeywordsStoppingCriteria

from PIL import Image
import math


def split_list(lst, n):
    """Split a list into n (roughly) equal-sized chunks"""
    chunk_size = math.ceil(len(lst) / n)  # integer division
    return [lst[i:i+chunk_size] for i in range(0, len(lst), chunk_size)]


def get_chunk(lst, n, k):
    chunks = split_list(lst, n)
    return chunks[k]


def annotate(args):
    # Model
    disable_torch_init()
    model_path = os.path.expanduser(args.model_path)
    model_name = get_model_name_from_path(model_path)
    tokenizer, model, image_processor, context_len = load_pretrained_model(model_path, args.model_base, model_name)

    answers = [json.loads(a) for a in open(os.path.expanduser(args.answers_file), "r")]
    questions = [json.loads(q) for q in open(os.path.expanduser(args.questions_file), "r")]
    while len(questions) > 0:
        traj_name_init = questions[0]["image"].strip("/*.jpg")
        traj_name = traj_name_init
        traj_len = 0
        while traj_name == traj_name_init:
            traj_len += 1
            traj_name = questions[traj_len]["image"].strip("/.jpg")
            print(traj_name)
        
        traj_ans = answers[:traj_len]
        answers = answers[traj_len:]
        questions = questions[traj_len:]

        
        print("Number of observations: ",   len(traj_ans))
        ans = "Summarize the path taken by a robot that has the following image observation descriptions in a concise single sentence:"
        for line in tqdm(traj_ans):
            an = line["text"]
            ans = ans + " " + str(an) + ","
        cur_prompt = ans
        if model.config.mm_use_im_start_end:
            ans = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN + '\n' + ans
        else:
            ans = DEFAULT_IMAGE_TOKEN + '\n' + ans

        conv = conv_templates[args.conv_mode].copy()
        conv.append_message(conv.roles[0], ans)
        conv.append_message(conv.roles[1], None)
        prompt = conv.get_prompt()

        # input_ids = tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors='pt').unsqueeze(0).cuda()
        input_ids = tokenizer(prompt, return_tensors="pt")
        input_ids = input_ids["input_ids"].cuda()

        # image = Image.open(image_file)
        # image_tensor = image_processor.preprocess(image, return_tensors='pt')['pixel_values'][0]

        stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
        keywords = [stop_str]
        stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)

        with torch.inference_mode():
            output_ids = model.generate(
                input_ids,
                do_sample=True if args.temperature > 0 else False,
                temperature=args.temperature,
                top_p=args.top_p,
                num_beams=args.num_beams,
                max_new_tokens=1024,
                use_cache=True)

        input_token_len = input_ids.shape[1]
        n_diff_input_output = (input_ids != output_ids[:, :input_token_len]).sum().item()
        if n_diff_input_output > 0:
            print(f'[Warning] {n_diff_input_output} output_ids are not the same as the input_ids')
        outputs = tokenizer.batch_decode(output_ids[:, input_token_len:], skip_special_tokens=True)[0]
        outputs = outputs.strip()
        if outputs.endswith(stop_str):
            outputs = outputs[:-len(stop_str)]
        outputs = outputs.strip()

        ans_file = open(os.path.join(traj_name_init, "lang.json"), "w")
        ans_id = shortuuid.uuid()
        ans_file.write(json.dumps({"traj_name": traj_name_init.split("/")[-1],
                                   "text": outputs,
                                   "raw_prompts" : traj_ans,
                                   "answer_id": ans_id,
                                   "model_id": model_name,
                                   "metadata": {}}) + "\n")
        print("Response: ", outputs)
        breakpoint()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-path", type=str, default="facebook/opt-350m")
    parser.add_argument("--model-base", type=str, default=None)
    parser.add_argument("--image-folder", type=str, default="")
    parser.add_argument("--question-file", type=str, default="")
    parser.add_argument("--answers-file", type=str, default="answer.jsonl")
    parser.add_argument("--conv-mode", type=str, default="llava_v1")
    parser.add_argument("--num-chunks", type=int, default=1)
    parser.add_argument("--chunk-idx", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.2)
    parser.add_argument("--top_p", type=float, default=None)
    parser.add_argument("--num_beams", type=int, default=1)
    args = parser.parse_args()

    annotate(args)
