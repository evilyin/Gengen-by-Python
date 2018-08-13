#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gengen import request_get, request_post, base_url, token_param
import json
import time

access_token = ""


def reply_mail(index, title, content):
    url = base_url + "/mail/inbox/reply/" + str(index) + ".json"
    data = {'oauth_token': access_token, 'title': title, 'content': content, 'backup': 1}
    request_post(url, data)
    # print(title + ":" + content)


def dy(user, content, index):
    if len(content) < 2:
        reply_mail(index, "追踪用户失败", "没有用户id")
        return
    target = content[1:]
    content_mail = u"当前已追踪用户："
    with open("db.txt", "a+") as db_file:
        db_file.seek(0, 0)
        db_str = db_file.read()
        if db_str == "":
            db_str = "{}"
        db = json.loads(db_str)
        if user in db:
            for tar in target:
                if tar not in db[user]:
                    db[user].append(tar)
        else:
            db[user] = target
        content_mail += ",".join(db[user])
        # 写入文件
        db_file.seek(0, 0)
        db_file.truncate()
        db_file.write(json.dumps(db))

    reply_mail(index, "追踪用户成功", content_mail.encode("utf-8"))


def td(user, content, index):
    target = content[1:]
    content_mail = u"当前已追踪用户："
    with open("db.txt", "a+") as db_file:
        db_file.seek(0, 0)
        db_str = db_file.read()
        if db_str == "":
            return
        db = json.loads(db_str)
        if user in db:
            if len(target) > 0:
                for tar in target:
                    if tar in db[user]:
                        db[user].remove(tar)
                        content_mail += ",".join(db[user])
            else:
                del db[user]
                content_mail += u"无"
        else:
            reply_mail(index, "退订失败", "你没有追踪过用户")
            return
        # 写入文件
        db_file.seek(0, 0)
        db_file.truncate()
        db_file.write(json.dumps(db))

    reply_mail(index, "退订成功", content_mail.encode("utf-8"))


def intro(index):
    title = "专业论坛机器人使用说明"
    content = """
    追踪发帖功能：
    追踪某个id一天内发的所有帖子和回复，每天早上记录前一天的帖子并发送站内信到你的邮箱。
    站内信发送内容 DY id 即可追踪该id的发帖，多个id用空格分割，例：
    DY IamRobot
    站内信发送内容 TD id 即可退订该id，多个id用空格分割，如果仅发送 TD 则退订全部id
    （追踪发帖功能不包含"本站站务"分区下的所有版面）
    
    声明：
    本机器人不是管理员，不能获取到除了id等公开信息以外的任何个人信息，并保证用户隐私安全，请放心使用。
    """
    reply_mail(index, title, content)
    print("intro")


def handle_mail():
    inbox = json.loads(request_get(base_url + "/mail/inbox" + token_param + access_token))
    for mail in inbox['mail']:
        mail_info = json.loads(request_get(base_url + "/mail/inbox/" + str(mail['index']) + token_param + access_token))
        con_str = mail_info['content'].partition(u"【")
        content = con_str[0].split()
        if len(content) > 0:
            if content[0] == "DY" or content[0] == "dy":
                dy(mail_info['user']['id'], content, mail_info['index'])
            elif content[0] == "TD" or content[0] == "td":
                td(mail_info['user']['id'], content, mail_info['index'])
            else:
                intro(mail['index'])
        else:
            intro(mail['index'])
        data = {'oauth_token': access_token}
        request_post(base_url + "/mail/inbox/delete/" + str(mail['index']) + ".json", data)
        print("handle mail done, mail deleted")
        time.sleep(6)


if __name__ == '__main__':
    try:
        with open("token.txt") as token_file:
            token_info = json.loads(token_file.read())
            access_token = token_info['access_token']
    except IOError:
        print("token read failed")

    info = json.loads(request_get(base_url + "/mail/info" + token_param + access_token))
    if info['new_mail'] is True:
        handle_mail()
