# src/toutiao_uploader/uploader.py
import requests
import base64
import qrcode
import io
import qrcode_terminal
from PIL import Image
import time
import os
from pyfiglet import figlet_format

class ToutiaoUploader:
    def __init__(self):
        self.token = None
        self.qrcode_url = None
        # 初始化
        pass
    
    def login(self):
        print("欢迎使用今日头条视频上传工具！")
        print("请选择登录方式：")
        print("1. 手机号登录")
        print("2. 二维码登录")
        choice = input("请输入您的选择：")
        if choice == "1":
            self.login_with_phone()
        elif choice == "2":
            self.login_with_qrcode()
        else:
            print("无效的选择，请重新选择。")

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

    def login_with_phone(self):
        phone_number = input("请输入您的手机号: ")
        # 假设在此处发送验证码并验证
        verification_code = input(f"已发送验证码到 {phone_number}，请输入验证码：")
        # 在此添加实际的验证逻辑
        if verification_code == "1234":  # 示例验证
            print("登录成功！")
            self.is_logged_in = True
            self.save_cookies()
        else:
            print("验证码错误，请重试。")

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
                    self.save_cookies_from_redirect(redirect_url,'user_cookies')
                    return True
                else:
                    print("未找到redirect_url。")                    
            elif data["status"] == "5":
                print("二维码已过期，重新生成二维码...")
                print(self.token)
        return False

    def save_cookies_from_redirect(self, url, file_name):
        # 创建 cookies 文件夹路径
        folder_path = os.path.join(os.getcwd(), 'cookies')
        os.makedirs(folder_path, exist_ok=True)  # 如果不存在，则创建文件夹

        # 文件完整路径
        file_path = os.path.join(folder_path, f"{file_name}.txt")

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
    def upload_video(self, file_path):
        # 处理视频上传逻辑
        print(f"正在上传视频文件 {file_path}...")
        # 在此添加上传 API 请求的逻辑