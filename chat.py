#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gengen import request_get, request_post, request_get_throw_error, base_url, token_param
import urllib2
import json
import uuid
import time

access_token = ""

cuid = "gengen_1"
appid = "dm7C361E5B4B62D97E"
appkey = "EE8D8A966D80836D02A2522A1DF6F8BF"

b_data = {
    'appid': appid,
    'appkey': appkey,
    'sdk_ui': "no",
    'sdk_init': "no",
    'appname': "com.evilyin.gengen",
    'channel_from': "",
    'channel_ctag': "",
    'from_client': "sdk",
    'hint_id': "",
    'CUID': cuid,
    'OLD_CUID': cuid,
    'StandbyDeviceId': cuid,
    'operation_system': "android",
    'sample_name': "bear_brain_wireless",
    'request_uid': cuid,
    'app_ver': "2.0.4.3",
    'query_type': "1",
    'network_status': "1_0",
    'ais_switch': 0,
    'BDUSS': "",
    'location_system': "wgs84",
    'longitude': 116.26626688264683,
    'latitude': 40.040987090358215,
    'debug': "0",
    'device_model': "MI NOTE LTE",
    'device_brand': "Xiaomi"
}


def request_post_with_header(url, data):
    header = {"HOST": "xiaodu.baidu.com", "Content-Type": "application/octet-stream", "User-Agent": "DcsSdk/1.5.0"}
    request = urllib2.Request(url, json.dumps(data), header)
    res_data = urllib2.urlopen(request)
    res = res_data.read()
    print(res)
    return res


def handle_refer(refer_type):
    info = json.loads(request_get(base_url + "/refer/" + refer_type + "/info" + token_param + access_token))
    if info['new_count'] > 0:
        refer_res = json.loads(
            request_get(
                base_url + "/refer/" + refer_type + token_param + access_token + "&count=" + str(info['new_count'])))
        for article in refer_res['article']:
            # 防止帖子被删，bad request
            try:
                con = get_content(article['board_name'], article['id'])
            except StandardError as err:
                print(err.args)
            else:
                b_data['client_msg_id'] = str(uuid.uuid4())
                b_data['request_query'] = con
                duer_reply = json.loads(request_post_with_header("https://xiaodu.baidu.com/saiya/ws2", b_data))
                reply_content = "Re:" + article['user']['id'] + "\n" + duer_reply['result']['speech']['content']
                post_reply(article['board_name'], reply_content, article['id'])
            # 设置提醒已读
            url_read = base_url + "/refer/" + refer_type + "/setRead/" + str(
                article['index']) + token_param + access_token
            request_post(url_read, {})
            time.sleep(6)


def get_content(board, article_id):
    url_c = base_url + "/article/" + board + "/" + str(article_id) + token_param + access_token
    art_detail = json.loads(request_get_throw_error(url_c))
    con = art_detail['content'].partition("--")
    con = con[0].partition(u"【")
    return con[0].replace("@IamRobot", "")


def post_reply(board, content, reid):
    url = base_url + "/article/" + board + "/post.json"
    content = content.encode('utf-8')
    data = {'title': "", 'content': content, 'reid': reid, 'oauth_token': access_token}
    request_post(url, data)


if __name__ == '__main__':
    # b_data['client_msg_id'] = str(uuid.uuid4())
    # b_data['request_query'] = ""
    # request_post_with_header("https://xiaodu.baidu.com/saiya/ws2", b_data)

    with open("token.txt") as token_file:
        token_info = json.loads(token_file.read())
        access_token = token_info['access_token']

    handle_refer("reply")
    handle_refer("at")
