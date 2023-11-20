import os 
import json


def file_num(file):
    if file.endswith('.jpg'):
        return int(file.split('.')[0])
    else:
        return 0


question_obs = "This is an observation from the perspective of a robot. Describe the image noting any specific objects or structures in a single sentence and be concise."
question_act = "These are three consecutive observations from the perspective of a robot. Describe the motion of the robot."
question_file = "/home/cglossop/LLaVA/annotate_w_llava/sacson_questions.jsonl"
input_dataset = "/home/cglossop/sacson"

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
            question_dir["text_obs"] = question_obs 
            question_dir["text_act"] = question_act
            with open(question_file, 'a+') as fp:
                json.dump(question_dir, fp)
                fp.write("\n")
        


