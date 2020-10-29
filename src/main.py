import sys
import cv2
import pyocr
import requests
import io
import os
import numpy as np
import pandas as pd
import urllib.request
from PIL import Image
import re
import subprocess
import argparse
import glob
import datetime


def extract_info(jsonl_path, out_dir):
    df = pd.read_json(jsonl_path, orient='records', lines=True)
    media_df = df[~df['media'].isnull()]
    print (media_df)
    tool = pyocr.get_available_tools()[0]
    for index_tweet,row in enumerate(media_df.itertuples()):
        print (index_tweet, row)
        if not row.media:
            continue
        tw_id = str(row.id)
        for index_media, media_values in enumerate(row.media):
            mail_results = []
            url_results = []
            domain_results = []
            phone_results = []
            if media_values['type'] != 'photo':
                continue
            try:
                img = Image.open(io.BytesIO(requests.get(media_values['fullUrl']).content))
                img_gray = img.convert("L")
                ocr_text = tool.image_to_string(
                    img_gray,
                    lang="jpn+eng",
                    builder=pyocr.builders.TextBuilder(tesseract_layout=6)
                    )
                # text_append
                extract_texts = []
                extract_texts.append(ocr_text.replace(os.linesep, ' '))
                extract_texts.append(ocr_text.replace(os.linesep, ''))

                # regex_pattern
                mail_pattern = re.compile("[-_a-zA-Z0-9\.+]+@[-a-zA-Z0-9\.]+")
                url_pattern = re.compile("https?://[\w!\?/\+\-_~=;\.,\*&@#\$%\(\)'\[\]]+")
                domain_pattern = re.compile("(([\da-zA-Z])([_\w-]{,62})\.){,127}(([\da-zA-Z])[_\w-]{,61})?([\da-zA-Z]\.((xn\-\-[a-zA-Z\d]+)|([a-zA-Z\d]{2,})))")
                phone_pattern = re.compile("0\d{9,10}")
                for extract_text in extract_texts:
                    # mail_check
                    results = mail_pattern.search(extract_text)
                    if results:
                        mail_domain = results.group().split("@")[1]
                        cmd_result = subprocess.run(["whois", mail_domain], stdout=subprocess.PIPE).stdout.decode("utf-8")
                        if ('No Object Found' not in cmd_result) and ('No whois server is known for this kind of object.' not in cmd_result):
                            if mail_domain not in white_list[0]:
                                mail_results.append(results.group())
                                if not os.path.exists(out_dir):
                                    os.mkdir(out_dir)
                                if not os.path.exists(image_dir):
                                    os.mkdir(image_dir)
                                image_dir = out_dir + 'image/'
                                image_path = image_dir + '{}_{}.jpg'.format(tw_id, index_media)
                                img.save(image_path, quality=100)
                    # url_check
                    results = url_pattern.search(extract_text)
                    if results:
                        url_domain = results.group().split("/")[2]
                        cmd_result = subprocess.run(["whois",url_domain], stdout=subprocess.PIPE).stdout.decode("utf-8")
                        if ('No Obeject Found' not in cmd_result) and ('No whois server is known for this kind of object.' not in cmd_result):
                            if url_domain not in white_list[0]:
                                url_results.append(results.group())
                                if not os.path.exists(out_dir):
                                    os.mkdir(out_dir)
                                if not os.path.exists(image_dir):
                                    os.mkdir(image_dir)
                                image_dir = out_dir + 'image/'
                                image_path = image_dir + '{}_{}.jpg'.format(tw_id, index_media)
                                img.save(image_path, quality=100)
                    # domain_check
                    results = domain_pattern.search(extract_text)
                    if results:
                        cmd_result = subprocess.run(["whois",results.group()], stdout=subprocess.PIPE).stdout.decode("utf-8")
                        if ('No Object Found' not in cmd_result) and ('No whois server is known for this kind of object.' not in cmd_result):
                            if results.group() not in white_list[0]:
                                domain_results.append(results.group())
                                if not os.path.exists(out_dir):
                                    os.mkdir(out_dir)
                                image_dir = out_dir + 'image/'
                                if not os.path.exists(image_dir):
                                    os.mkdir(image_dir)
                                image_path = image_dir + '{}_{}.jpg'.format(tw_id, index_media)
                                img.save(image_path, quality=100)
                    # phone_check
                    results = phone_pattern.search(extract_text)
                    if results:
                        if results.group() not in white_list[1]:
                            if not os.path.exists(out_dir):
                                os.mkdir(out_dir)
                            image_dir = out_dir + 'image/'
                            if not os.path.exists(image_dir):
                                os.mkdir(image_dir)
                            image_path = image_dir + '{}_{}.jpg'.format(tw_id, index_media)
                            img.save(image_path, quality=100)

                            phone_results.append(results.group())
                # ここからpathを書く
                mail_dir = out_dir + 'mail/'
                url_dir = out_dir + 'url/'
                domain_dir = out_dir + 'domain/'
                phone_dir = out_dir + 'phone/'

                mail_path = mail_dir + '{}_{}.txt'.format(tw_id,index_media)
                url_path = url_dir + '{}_{}.txt'.format(tw_id,index_media)
                domain_path = domain_dir + '{}_{}.txt'.format(tw_id,index_media)
                phone_path = phone_dir + '{}_{}.txt'.format(tw_id,index_media)
                detect_flag = False
                if mail_results:
                    detect_flag = True
                    if not os.path.exists(mail_dir):
                        os.mkdir(mail_dir)
                    with open(mail_path,'w') as f:
                        f.write('\n'.join(list(set(mail_results))))
                if url_results:
                    detect_flag = True
                    if not os.path.exists(url_dir):
                        os.mkdir(url_dir)
                    with open(url_path, 'w') as f:
                        f.write('\n'.join(list(set(url_results))))
                if domain_results:
                    detect_flag = True
                    if not os.path.exists(domain_dir):
                        os.mkdir(domain_dir)
                    with open(domain_path, 'w') as f:
                        f.write('\n'.join(list(set(domain_results))))
                if phone_results:
                    detect_flag = True
                    if not os.path.exists(phone_dir):
                        os.mkdir(phone_dir)
                    with open(phone_path, 'w') as f:
                        f.write('\n'.join(list(set(phone_results))))
                if detect_flag:
                    json_dir = out_dir + 'json/'
                    if not os.path.exists(json_dir):
                        os.mkdir(json_dir)
                    json_path = json_dir + '{}.json'.format(tw_id)
                    media_df[media_df['id'] == int(tw_id)].to_json(json_path)
                    print ('Detected')
                else:
                    print ('Not Detected')
            except:
                import traceback
                traceback.print_exc()
                continue


if __name__ == "__main__":
    # example
    # -d ./domain.txt -p ./phone.txt json ./ja_ntt_sagi.jsonl out /var/nfs/exports/
    parser = argparse.ArgumentParser(description='get information')
    # domain_white_list
    parser.add_argument('-d','--domain')
    # phone_white_list
    parser.add_argument('-p','--phone')
    # jsonl_path
    parser.add_argument('-j','--json')
    # out_path
    parser.add_argument('-o','--out')
    # check_minutes
    parser.add_argument('-s', '--seconds', type=int, default=900)
    args = parser.parse_args()
    white_list_path = [args.domain, args.phone]
    white_list = []
    for path in white_list_path:
        white = []
        with open(path,'r') as f:
            for line in f:
                white.append(line.strip())
        white_list.append(white)
    jsonl_list = glob.glob(args.json)
    check_json_list = []
    dt_now = datetime.datetime.now()
    out_path = args.out.rstrip('/') + '/' + dt_now.strftime('%Y-%m-%dT%H-%M-%S') + '/'
    for json_name in jsonl_list:
        check_time = json_name.split("/")[-1].split(".")[0].split("_")[-1]
        dt_check = datetime.datetime.strptime(check_time, '%Y-%m-%dT%H:%M:%S')
        check_minute = (dt_now - dt_check).seconds
        if check_minute <= args.seconds:
            check_json_list.append(json_name)
    print (check_json_list)
    for check_json_path in check_json_list:
        if os.stat(check_json_path).st_size > 0:
            extract_info(check_json_path, out_path)
