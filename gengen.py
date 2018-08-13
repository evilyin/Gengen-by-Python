#!/usr/bin/env python
# -*- coding: utf-8 -*-
import urllib
import urllib2
import json
import time


INTERVAL = 300
CLIENT_ID = "48bf3ea8aab5256baf22d175aebce5fa"
CLIENT_SECRET = "2c08a8c193a34af98add4be7d90766ce"

access_token = ""
refresh_token = ""
base_url = "http://bbs.byr.cn/open"
token_param = ".json?oauth_token="
sections = []
log_string = ""
id_list = []

reply_content = """专业论坛机器人  v1.0.1 修复了一些小bug
想每天掌握关心的人的最新发帖吗？专业论坛机器人帮你实现！给本账号发站内信获取使用方法，马上开启论坛新玩法！
【持续研发中  欢迎提出建议及反馈bug】"""


# reply_content = "专业论坛机器人，新功能研发中，敬请期待"


def request_get(url):
    try:
        request = urllib2.Request(url)
        res_data = urllib2.urlopen(request)
    except StandardError as err:
        print(err.args)
        time.sleep(20)
        return request_get(url)
    else:
        res = res_data.read()
        # print(res)
        return res


def request_post(url, data):
    request = urllib2.Request(url, urllib.urlencode(data))
    res_data = urllib2.urlopen(request)
    res = res_data.read()
    print(res)
    return res


def post_reply(board, content, reid):
    url = base_url + "/article/" + board + "/post.json"
    data = {'title': "", 'content': content, 'reid': reid, 'oauth_token': access_token}
    request_post(url, data)


def search_thread(board, name):
    # print("searching:" + board)
    url = base_url + "/search/threads" + token_param + access_token + "&board=" + board + "&author=" + name + "&day=2"
    search_result = json.loads(request_get(url))
    if search_result['pagination']['item_all_count'] != 0:
        for each_thread in search_result['threads']:
            if time.time() - each_thread['post_time'] < INTERVAL + 60:
                # 当前时间减去发帖时间小于搜索间隔，可能发现新帖，验证id
                if each_thread['id'] in id_list:
                    continue
                id_list.append(each_thread['id'])
                post_reply(each_thread['board_name'], reply_content, each_thread['id'])
                global log_string
                log_string += time.strftime('%Y-%m-%d %H:%M:%S') \
                              + "\n" + u"发现新帖：" + each_thread['title'] \
                              + u" 版面：" + each_thread['board_name'] \
                              + u" 发帖时间：" + time.strftime('%Y-%m-%d %H:%M:%S',
                                                          time.localtime(each_thread['post_time'])) + "\n"
                time.sleep(6)


def search_article(board, name, result_list, page=1):
    print("searching target " + name + " in board " + board)
    url = base_url + "/search/article" + token_param + access_token + "&board=" + board + "&author=" + name \
          + "&day=1" + "&page=" + str(page)
    search_result = json.loads(request_get(url))
    if search_result['pagination']['item_all_count'] != 0:
        result_list.append(name + ":\n")
    else:
        return
    for each_article in search_result['article']:
        url_c = base_url + "/article/" + board + "/" + str(each_article['id']) + token_param + access_token
        art_detail = json.loads(request_get(url_c))
        con = art_detail['content'].split()
        st = u"标题：" + art_detail['title'] + "\n" + con[0] + "\n" \
             + "[url=https://bbs.byr.cn/#!article/" + board + "/" + str(art_detail['group_id']) + "?s=" + str(
            art_detail['id']) + u"][color=#0000FF]点击打开原帖[/color][/url]\n"
        result_list.append(st)

    if search_result['pagination']['page_all_count'] > search_result['pagination']['page_current_count']:
        # 有分页，没到最后一页
        search_article(board, name, result_list, page + 1)


def get_section(name):
    if name == "BYRBT":  # 忽略BT分区
        return []
    url = base_url + "/section/" + str(name) + token_param + access_token
    section_json = json.loads(request_get(url))
    board_list = []
    if len(section_json['sub_section']) > 0:
        for section in section_json['sub_section']:
            # 递归查找子分区
            board_list.extend(get_section(section))
    # 版面名记录在列表中
    for board in section_json['board']:
        board_list.append(board['name'])
    return board_list


def send_mail(user_id, title, content):
    url = base_url + "/mail/send.json"
    data = {'id': user_id, 'title': title, 'content': content, 'backup': 1, 'oauth_token': access_token}
    request_post(url, data)


if __name__ == '__main__':
    # 读取token
    try:
        with open("token.txt") as token_file:
            token_info = json.loads(token_file.read())
            access_token = token_info['access_token']
            refresh_token = token_info['refresh_token']
    except IOError:
        print("token read failed")

    # 刷新token
    req_data = {'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET, 'grant_type': "refresh_token",
                'refresh_token': refresh_token}
    resp = request_post("http://bbs.byr.cn/oauth2/token", req_data)

    # 保存token
    try:
        with open("token.txt", "w+") as token_file:
            token_file.write(resp)
            token_file.flush()
    except IOError:
        print("token write failed")

    # 搜索全分区
    for i in range(0, 10):
        sections.append(get_section(i))

    # Professional Forum Robot
    try:
        with open("db.txt") as db_file:
            db = json.loads(db_file.read())
            for user in db:
                result = []
                for target in db[user]:
                    print("searching user:" + user)
                    for s in range(1, 10):
                        for each_board in sections[s]:
                            search_article(each_board, target, result)
                if len(result) > 0:
                    r = "\n".join(result)
                    # print(r)
                    send_mail(user, "你关心的人又发帖啦", r.encode("utf-8"))
    except StandardError as e:
        print(e.args)
        print(e.message)

    # gengen
    for t in range(80):
        print("start searching, times:%d" % t)
        for s in range(3, 9):
            for each_board in sections[s]:
                search_thread(each_board, "guitarmega")
        if log_string != "":
            send_mail("evilyin", "gengen log", log_string.encode("utf-8"))
            log_string = ""
        time.sleep(INTERVAL)
