#!/usr/bin/python3

# Copyright (c) 2021, Jan Varho

import boto3
import json
import os
import requests
import traceback


s3 = boto3.resource('s3')
bucket = s3.Bucket(os.getenv('BUCKET'))

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirect_url = os.getenv('API_URL') + '/authorize'


def get_ltt(token):
    url = (
        'https://graph.instagram.com/access_token?' +
        'grant_type=ig_exchange_token&' +
        'client_secret=%s&' % client_secret +
        'access_token=%s' % token
    )
    r = requests.get(url)
    return r.json()


def get_token(code):
    url = 'https://api.instagram.com/oauth/access_token'
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_url,
        'code': code,
    }
    r = requests.post(url, data)
    j = r.json()
    ltt = get_ltt(j.get('access_token'))
    j.update(ltt)
    return j


def refresh_token(token):
    url = (
        'https://graph.instagram.com/refresh_access_token?' +
        'grant_type=ig_refresh_token&' +
        'access_token=%s' % token.get('access_token')
    )
    r = requests.get(url)
    j = r.json()
    token.update(j)
    return token


def get_data(token):
    url = (
        'https://graph.instagram.com/me/media?' +
        'fields=id,caption,media_url,permalink,thumbnail_url,timestamp,username&' +
        'access_token=' + token
    )
    r = requests.get(url)
    return r.json()


def load_tokens():
    bucket.download_file('tokens.json', '/tmp/tmp.json')
    with open('/tmp/tmp.json') as f:
        return json.load(f)


def load_token(i):
    return load_tokens().get(i)


def save_token(data):
    try:
        tokens = load_tokens()
    except:
        tokens = {}
    tokens[data.get('user_id')] = data
    bucket.put_object(Body=json.dumps(tokens).encode(),
                      Key='tokens.json')


def authorize(event, *args, **kwargs):
    params = event.get('queryStringParameters', {})

    code = params.get('code')
    if not code:
        return {
            'isBase64Encoded': False,
            'statusCode': 307,
            'body': 'Temporary Redirect',
            'headers': {
                'Location': (
                    'https://www.instagram.com/oauth/authorize?' +
                    'client_id=%s&' % client_id +
                    'redirect_uri=%s&' % redirect_url +
                    'scope=user_profile,user_media&' +
                    'response_type=code'
                )
            }
        }

    try:
        token = get_token(code)
        save_token(token)
    except Exception:
        traceback.print_exc()
        return {'status': 'ERROR'}

    return {'status': 'OK'}


def load(event, *args, **kwargs):
    params = event.get('queryStringParameters', {})

    try:
        i = params.get('user_id')
        token = load_token(i)
        data = get_data(token.get('access_token'))
        return {
            'status': 'OK',
            'data': sorted(data.get('data'), key=lambda d: d.get('timestamp'), reverse=True)
        }
    except Exception:
        traceback.print_exc()
        return {'status': 'ERROR'}


def refresh(*args, **kwargs):
    try:
        for token in load_tokens().values():
            token = refresh_token(token)
            save_token(token)
        return {
            'status': 'OK'
        }
    except Exception:
        raise
