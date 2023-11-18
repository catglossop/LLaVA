import os 
import json


def file_num(file):
    if file.endswith('.jpg'):
        return int(file.split('.')[0])
    else:
        return 0


question_obs = "This is an observation from the Describe the image in a single sentence and be concise."
question_act = "What is the action being performed in the image?"
question_file = "/home/cglossop/LLaVa/annotate_w_llava/gnm_questions_1_traj_sorted.jsonl"
input_dataset = "/home/cglossop/gnm_dataset/sacson/Dec-06-2022-bww8_00000000_0"

question_cnt = 0
for root, dirs, files in os.walk(input_dataset):

    for file in sorted(files, key=lambda file: file_num(file)):
        image_path = os.path.join(root, file)
        if file.endswith('.jpg'):
            print(file)
            file_name = file.split('.')[0]
            question_dir = {}
            question_dir = {"question_id" : question_cnt}
            question_cnt += 1

            question_dir["image"] = image_path
            question_dir["text"] = question 
            with open(question_file, 'a+') as fp:
                json.dump(question_dir, fp)
                fp.write("\n")
        


