# apps/utils/yunpian.py

import requests
import json

class YunPian(object):

    def __init__(self, api_key):
        self.api_key = api_key
        self.single_send_url = "https://sms.yunpian.com/v2/sms/single_send.json"

    def send_sms(self, code, mobile):
        #需要传递的参数
        parmas = {
            "apikey": self.api_key,
            "mobile": mobile,
            "text": "【慕雪生鲜超市】您的验证码是{code}。如非本人操作，请忽略本短信".format(code=code)
        }

        response = requests.post(self.single_send_url, data=parmas)
        re_dict = json.loads(response.text)
        return re_dict

if __name__ == "__main__":
    #例如：9b11127a9701975c734b8aee81ee3526
    yun_pian = YunPian("2e87d17327d4be01608f7c6da23ecea2")
    yun_pian.send_sms("2018", "手机号码")



