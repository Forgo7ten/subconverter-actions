import requests
import sys
import copy
import json
import base64
import os
from urllib.parse import quote
from datetime import datetime, timedelta


g_github_token = ""  # GitHub Token
g_gist_id = ""  # gist id


def create_gist(filecontent_dict):
    '''
    创建gist，没用
    '''
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {g_github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = "https://api.github.com/gists"
    data = {
        "description": "subconverter-action",
        "public": False,
        "files": {
        }
    }
    for gist_filename, gist_content in filecontent_dict.items():
        data["files"][gist_filename] = {"content": gist_content}
    response = requests.post(url, headers=headers, json=data)
    print(response.status_code)
    print(response.json())


def update_gist(gist_id, filecontent_dict):
    '''
    更新gist
    '''
    global g_github_token
    global headers
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {g_github_token}",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    url = f"https://api.github.com/gists/{gist_id}"
    data = {
        "description": "subconverter-actions",
        "files": {
        }
    }
    for gist_filename, gist_content in filecontent_dict.items():
        if gist_content is None:
            # 删除文件
            data["files"][gist_filename] = None
        else:
            data["files"][gist_filename] = {"content": gist_content}
    response = requests.patch(url, headers=headers, data=json.dumps(data))
    print(f"update_gist response:{response.status_code}")
    # print(response.json())



def convert_subscribe(subscribe_dict):
    base_url = "http://localhost:25500/sub"
    filecontent_dict = {}
    for filename, params in subscribe_dict.items():
        url = f"{base_url}{params}"
        response = requests.get(url)
        filecontent_dict[filename] = response.text+f"\n\n# Updated on {(datetime.now()+timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')}\n" # 展示UTC/GMT +8.00的时间
    return filecontent_dict

def test_param():
    '''
    生成参数
    '''
    template_params = "?target=clash&insert=false&exclude=%E5%A5%97%E9%A4%90%E5%88%B0%E6%9C%9F%7C%E8%8A%82%E7%82%B9%E8%B6%85%E6%97%B6%7C%E6%9B%B4%E6%8D%A2%7C%E5%89%A9%E4%BD%99%E6%B5%81%E9%87%8F%7C%E5%88%B0%E6%9C%9F%E6%97%B6%E9%97%B4%7CTG%E7%BE%A4%7C%E5%AE%98%E7%BD%91&interval=259200&emoji=true&list=true&xudp=false&udp=true&tfo=false&expand=true&scv=true&fdn=false&new_name=true&url="
    subscribe_url = {
        # "template.yml":"https://ooxx/subscribe?token=xxxxx",
    }
    subscribe_dict = {}
    for filename, url in subscribe_url.items():
        subscribe_dict[filename] = template_params + quote(url)
    convert_param = base64.b64encode(json.dumps(subscribe_dict).encode("utf-8")).decode("utf-8")
    print(f"CONVERT_PARAM={convert_param}")
    pass

if __name__ == "__main__":
    # test_param()
    try:
        subscribe_dict = json.loads(base64.b64decode(os.environ['CONVERT_PARAM']).decode("utf-8"))
    except Exception as e:
        print(f"{e}")
        sys.exit(1)
    g_github_token = os.environ['PERSONAL_TOKEN']
    g_gist_id = os.environ['GIST_ID']
    filecontent_dict = convert_subscribe(subscribe_dict)
    if g_github_token != "" and g_gist_id != "":
        update_gist(gist_id=g_gist_id,filecontent_dict=filecontent_dict)
        pass
    else:
        print("不上传gist")
    pass
