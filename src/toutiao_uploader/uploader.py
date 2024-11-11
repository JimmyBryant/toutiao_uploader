# src/toutiao_uploader/uploader.py
import requests
import base64
import qrcode
import io
from PIL import Image
import time
import os
import json
import random
import string
from datetime import datetime
import hmac
import hashlib
import binascii

class ToutiaoUploader:
    def __init__(self):
        self.username = None
        self.token = None
        self.qrcode_url = None
        self.base_url = "https://mp.toutiao.com/mp/agw/creator_center/user_info?app_id=1231"
        self.upload_init_url = "https://tos-d-x-hl.snssdk.com/upload/v1/tos-cn-v-0004/oQbADZFKmIDf5zAAVuTgfjEEnVJMRLtADCvtqB?uploadmode=part&phase=init"
        self.upload_url_template = "https://tos-d-x-hl.snssdk.com/upload/v1/tos-cn-v-0004/oQbADZFKmIDf5zAAVuTgfjEEnVJMRLtADCvtqB?uploadid={upload_id}&part_number={part_number}&phase=transfer&part_offset={part_offset}"
        self.publish_url = "https://mp.toutiao.com/xigua/api/upload/PublishVideo"
        # 初始化
        pass
    
    def login(self, username):
        print("欢迎使用今日头条视频上传工具！请扫码登录")   
        self.username = username     
        # 用户扫码
        self.login_with_qrcode()
    def get_user_info(self, username):
            # 从 cookies 文件加载
            cookie_file = os.path.join(os.getcwd(), 'cookies', f"{username}.txt")
            cookies = {}
            if os.path.exists(cookie_file):
                with open(cookie_file, 'r') as file:
                    cookies = {line.split('=')[0]: line.split('=')[1].strip() for line in file}
            headers = {
                "Cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()])
            }
            # 创建 user 目录
            user_dir = os.path.join(os.getcwd(), 'user')
            os.makedirs(user_dir, exist_ok=True)

            # 获取用户信息
            response = requests.get(self.base_url, headers=headers)
            if response.status_code == 200:
                user_info = response.json()
                if user_info["code"] == 0:
                    name = user_info.get("name", "unknown_user")
                    file_path = os.path.join(user_dir, f"{name}.txt")
                    
                    # 保存用户信息到文件
                    with open(file_path, 'w') as file:
                        json.dump(user_info, file, ensure_ascii=False, indent=4)
                    print(f"用户信息已保存到 {file_path}")
                else:
                    print("获取用户信息失败:", user_info.get("message", "未知错误"))
            else:
                print("请求失败，状态码:", response.status_code)

    """
        获取用户auth key
    """
    def get_auth_key(self,username):
        url = "https://mp.toutiao.com/xigua/api/upload/getAuthKey/"
        params = {
            "params": '{"type":"video","column":"false","ugc":"false","useImageX":"true","useStsToken":"true"}'
        }
        cookies = self.load_cookies_by_username(username)
        # Set headers, including cookies if required for auth
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "referer": "https://mp.toutiao.com/profile_v4/xigua/upload-video",
            "Cookie": "; ".join([f"{k}={v}" for k, v in cookies.items()])  # Ensure cookies are set properly
        }

        try:
            response = requests.get(url,params=params, headers=headers)
            response.raise_for_status()  # Raises an error if status is not 200
            auth_key_data = response.json()
            print(auth_key_data)  # Display the API response data
            return auth_key_data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching AuthKey: {e}")

    def get_signature_key(self, secret_key, date, region, service_name):
        """
        根据 AWS 签名版本 4 计算签名密钥
        :param secret_key: AWS Secret Access Key
        :param date: 当前日期（格式：yyyyMMdd）
        :param region: 区域（例如：cn-north-1）
        :param service_name: 服务名（例如：vod）
        :return: 签名密钥
        """
        key = f"AWS4{secret_key}".encode("utf-8")
        date_key = hmac.new(key, date.encode("utf-8"), hashlib.sha256).digest()
        region_key = hmac.new(date_key, region.encode("utf-8"), hashlib.sha256).digest()
        service_key = hmac.new(region_key, service_name.encode("utf-8"), hashlib.sha256).digest()
        signing_key = hmac.new(service_key, b"aws4_request", hashlib.sha256).digest()
        return signing_key

    """
        获取上传空间地址
    """
    def get_upload_space_url(self, username, video_path):
        # API 信息
        url = "https://vod.bytedanceapi.com"
        path = "/"
        service_name = "vod"
        region = "cn-north-1"
        action = "ApplyUploadInner"
        version = "2020-11-19"
        space_name = "pgc"
        file_type = "video"
        
        # 计算视频文件的大小
        video_size = os.path.getsize(video_path)

        # 调用get_auth_key函数获取auth_data
        auth_data = self.get_auth_key(username)

        # 从返回的数据中提取AccessKeyId和SecretAccessKey
        access_key = auth_data['data']['uploadToken']['AccessKeyId']
        secret_key = auth_data['data']['uploadToken']['SecretAccessKey']
        session_token = auth_data['data']['uploadToken']['SessionToken']


        # 打印出获取的access_key和secret_key，检查是否正确
        print("AccessKeyId:", access_key)
        print("SecretAccessKey:", secret_key)

        # 当前时间信息
        timestamp = datetime.utcnow()
        date = timestamp.strftime('%Y%m%d')
        amz_date = timestamp.strftime('%Y%m%dT%H%M%SZ')

        # 准备查询参数和 Headers
        params = {
            "Action": action,
            "Version": version,
            "SpaceName": space_name,
            "FileType": file_type,
            "IsInner": "1",
            "FileSize": str(video_size),
            "EnOID": "1",
            "app_id": "1231",
            "user_id": self.get_user_id(username),
            "s": ''.join(random.choices(string.ascii_letters + string.digits, k=8)),
        }

        headers = {
            "x-amz-date": amz_date,
            'x-amz-security-token': session_token,
            "x-amz-content-sha256": hashlib.sha256(b"").hexdigest()
        }

        # 创建 Credential String
        credential_scope = f"{date}/{region}/{service_name}/aws4_request"
        canonical_headers = "\n".join([f"{k}:{v}" for k, v in headers.items()]) + "\n"
        signed_headers = ";".join(headers.keys())

        # 构建 Canonical Request
        canonical_querystring = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        canonical_request = f"GET\n{path}\n{canonical_querystring}\n{canonical_headers}\n{signed_headers}\n{headers['x-amz-content-sha256']}"

        # 创建 String to Sign
        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"

        # 生成签名密钥
        signing_key = self.get_signature_key(secret_key, date, region, service_name)

        # 计算 Signature
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()

        # 创建 Authorization Header
        authorization_header = (
            f"AWS4-HMAC-SHA256 Credential={access_key}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        headers["Authorization"] = authorization_header

        # 发起请求
        response = requests.get(url, params=params, headers=headers)
        response_data = response.json()
        print(response_data)
        return response_data

    def get_user_id(self, username):
        # This function reads the user file and extracts the `user_id`
        file_path = os.path.join("user", f"{username}.txt")
        with open(file_path, 'r') as file:
            user_data = json.load(file)
        return user_data.get("user_id")

    def resize_qr_image(self, qr_input, size=(50, 50)):
        # 如果是URL，则生成二维码
        if qr_input.startswith('http'):
            qr_image = qrcode.make(qr_input)
        else:  # 如果是Base64，则解码
            qr_image_data = base64.b64decode(qr_input)
            qr_image = Image.open(io.BytesIO(qr_image_data))
        
        # 调整二维码尺寸
        resized_image = qr_image.resize(size, Image.LANCZOS)
        # 保存到项目中 
        output_path = os.path.join(os.getcwd(), 'resized_qr_code.png')
        resized_image.save(output_path, format="PNG")

        # 返回绝对路径
        return os.path.abspath(output_path)
        # 保存到内存并返回Base64编码
        # buffered = io.BytesIO()
        # resized_image.save(buffered, format="PNG")
        # resized_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
        # return resized_base64

    def display_qr_code(self, base64_code, size_ratio=1.0):
        # 解码 base64 编码的图像
        image_data = base64.b64decode(base64_code)
        img = Image.open(io.BytesIO(image_data))

        # 根据尺寸比例调整图像大小
        new_size = (int(img.width * size_ratio), int(img.height * size_ratio))
        img = img.resize(new_size, Image.LANCZOS)  # 使用 LANCZOS 代替 ANTIALIAS

        # 保存临时文件
        temp_image_path = "temp_qrcode.png"
        img.save(temp_image_path)

        # 使用 catimg 显示图像
        os.system(f'catimg {temp_image_path}')

        # 清理临时文件
        os.remove(temp_image_path)
    

    def display_qr_code_from_base64(self, base64_code):
        # 将Base64解码为图像
        image_data = base64.b64decode(base64_code)
        image = Image.open(io.BytesIO(image_data))
        image.show()  # 或者进行进一步处理，比如缩小尺寸、转换为ASCII等

    def get_qr_code(self):
        # 请求获取二维码的 API
        url = "https://sso.toutiao.com/get_qrcode/?service=https%3A%2F%2Fwww.toutiao.com%2F%3Fwid%3D1730548030059&need_logo=false&ui_version=3.2.1&aid=24&account_sdk_source=sso&sdk_version=2.2.5-beta.8&language=zh&verifyFp=verify_m303m6x5_RFowaRdd_mqcb_4vZy_8sQ8_Pzo6BfPsrvCR&fp=verify_m303m6x5_RFowaRdd_mqcb_4vZy_8sQ8_Pzo6BfPsrvCR"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("data", {})
            self.token = data.get('token')
            qrcode_url = data.get('qrcode_index_url')
            qrcode = data.get('qrcode')
            if qrcode_url:  # 确保 qrcode 是字符串
                self.display_qr_code_from_base64(qrcode)
            else:
                print("未获取到二维码。")
        else:
            print(f"请求失败，状态码：{response.status_code}")

    # 使用二维码登录
    def login_with_qrcode(self):
        self.get_qr_code()
        self.wait_for_login()

    def wait_for_login(self):
        print("正在等待扫码登录...")
        while True:
            if self.check_qr_status():
                break
            time.sleep(5)  # 每5秒检查一次
    def check_qr_status(self):
        url = f"https://sso.toutiao.com/check_qrconnect/?service=https%3A%2F%2Fwww.toutiao.com%2F%3Fwid%3D1730617604152&token={self.token}&need_logo=false&ui_version=3.2.1&aid=24&account_sdk_source=sso&sdk_version=2.2.5-beta.8&language=zh&verifyFp=verify_m3191erh_J2kLIOjM_eT1l_4DLF_BRBQ_TIdyQGpNXl4C&fp=verify_m3191erh_J2kLIOjM_eT1l_4DLF_BRBQ_TIdyQGpNXl4C"
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("data", {})
            print('是否扫码？',data)
            if data["status"] == "success":
                print("登录成功！")
                return True
            elif data["status"] == "1":
                print("等待扫码...")
            elif data["status"] == "3":
                # 当status为3时，使用redirect_url获取登录凭证
                redirect_url = data.get("redirect_url")
                print(redirect_url)
                if redirect_url:
                    self.save_cookies_to_file(redirect_url) # 保存cookies到文件
                    self.get_user_info(self.username)   # 获取用户信息
                    return True
                else:
                    print("未找到redirect_url。")                    
            elif data["status"] == "5":
                print("二维码已过期，重新生成二维码...")
                print(self.token)
        return False

    def save_cookies_to_file(self, url):
        # 创建 cookies 文件夹路径
        folder_path = os.path.join(os.getcwd(), 'cookies')
        os.makedirs(folder_path, exist_ok=True)  # 如果不存在，则创建文件夹

        # 文件完整路径
        file_path = os.path.join(folder_path, f"{self.username}.txt")

        # 请求并保存 Cookies
        session = requests.Session()
        response = session.get(url)
        if response.status_code == 200:
            with open(file_path, 'w') as file:
                for cookie in session.cookies:
                    file.write(f"{cookie.name}={cookie.value}\n")
            print(f"Cookies 已保存到 {file_path}")
        else:
            print("跳转失败，无法保存 Cookie")
   
   
    """
    从本地文件加载用户名对应的 Cookie
    """
    def load_cookies_by_username(self, username):
        cookie_file = os.path.join(os.getcwd(), 'cookies', f"{username}.txt")
        cookies = {}
        if os.path.exists(cookie_file):
            with open(cookie_file, 'r') as file:
                for line in file:
                    name, value = line.strip().split('=')
                    cookies[name] =value
        return cookies
    def load_cookies(self, file_path):
        cookies = {}
        with open(file_path, 'r') as file:
            for line in file:
                name, value = line.strip().split('=', 1)
                cookies[name] = value
        return cookies
    def publishWTT(self,content,  ms_token='', a_bogus='', image_list=None):
        url = f"https://mp.toutiao.com/mp/agw/article/wtt?msToken={ms_token}&a_bogus={a_bogus}"
        
        # 微头条的发布数据
        data = {
            "content": content,
            "image_list": image_list or [],
            "extra": "{\"claim_exclusive\":\"1\",\"add_music_to_article_flag\":\"0\",\"tuwen_wtt_trans_flag\":\"0\",\"info_source\":\"{\\\"source_type\\\":-1}\"}",
            "is_fans_article": 2,
            "pre_upload": 1,
            "welfare_card": ""
        }
        cookies_file = "cookies/user_cookies.txt"
        headers = {
            'Cookie': '; '.join([f"{k}={v}" for k, v in self.load_cookies(cookies_file).items()]),
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=data, headers=headers)
        
        if response.status_code == 200:
            print("微头条发布成功:", response.json())
        else:
            print("微头条发布失败，状态码:", response.status_code)
    def _initiate_upload(self):
        headers = {
            "Content-Type": "application/json",
        }
        response = requests.post(self.upload_init_url, headers=headers)
        response.raise_for_status()
        return response.json()["data"]["uploadid"]

    def _upload_chunk(self, upload_id, part_number, part_offset, chunk):
        upload_url = self.upload_url_template.format(upload_id=upload_id, part_number=part_number, part_offset=part_offset)
        response = requests.post(upload_url, headers=self.headers, data=chunk)
        response.raise_for_status()

    """
        分块上传视频
    """
    def upload_video_in_parts(self, username, video_path):
        # 获取上传地址信息
        upload_space_info = self.get_upload_space_url(username, video_path)
        upload_node = upload_space_info['Result']['InnerUploadAddress']['UploadNodes'][0]
        upload_host = upload_node['UploadHost']
        store_info = upload_node['StoreInfos'][0]
        store_uri = store_info['StoreUri']
        auth = store_info['Auth']

        # 初始化请求
        init_url = f"https://{upload_host}/upload/v1/{store_uri}?uploadmode=part&phase=init"
        boundary = "----WebKitFormBoundaryu04Gvna450BA9yOU"
        headers = {
            "Authorization": auth,
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site",
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
            "X-Storage-U": str(self.get_user_id(username)),
            "referer": "https://mp.toutiao.com/",
        }
        init_response = requests.post(init_url, headers={**headers, "Content-Type": f"multipart/form-data; boundary={boundary}","X-Storage-Mode": "gateway"}, data=f"--{boundary}--\r\n")
        init_response_data = init_response.json()
        upload_id = init_response_data['data']['uploadid']

        # 获取文件的总块数
        total_size = os.path.getsize(video_path)
        chunk_size = 10 * 1024 * 1024  # 每块大小设置为10MB
        total_parts = (total_size // chunk_size) + (1 if total_size % chunk_size != 0 else 0)

        with open(video_path, 'rb') as f:
            for part_number in range(1, total_parts + 1):
                data = f.read(chunk_size)
                if not data:
                    break

                # 每个块的上传URL
                part_url = (
                    f"https://{upload_host}/upload/v1/{store_uri}"
                    f"?uploadid={upload_id}&part_number={part_number}&phase=transfer"
                    f"&part_offset={chunk_size * (part_number - 1)}"
                )
                
                # 计算 Content-CRC32 值
                crc32_value = binascii.crc32(data) & 0xffffffff
                content_crc32 = format(crc32_value, '08x')

                # 上传块请求
                response = requests.post(part_url, headers={**headers, "Content-Type": "application/octet-stream", "Content-CRC32": content_crc32, "Content-Disposition": "attachment; filename=\"undefined\""}, data=data)
                if response.status_code != 200:
                    raise Exception(f"Failed to upload part {part_number}")

                # 打印进度
                response_data = response.json()
                etag = response_data['data']['etag']
                print(f"Uploaded part {part_number}/{total_parts}, ETag: {etag}")

        # 完成上传请求
        finish_url = f"https://{upload_host}/upload/v1/{store_uri}?uploadmode=part&phase=finish&uploadid={upload_id}"
        finish_response = requests.post(finish_url, headers=headers)
        if finish_response.status_code != 200:
            raise Exception("Failed to complete upload.")

        print("Upload completed successfully.")