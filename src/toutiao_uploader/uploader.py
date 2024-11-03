# src/toutiao_uploader/uploader.py
import requests
import base64
import qrcode
import io
import qrcode_terminal
from PIL import Image
import time
import os

class ToutiaoUploader:
    def __init__(self):
        self.token = None
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

    def get_qr_code(self):
        # 请求获取二维码的 API
        url = "https://sso.toutiao.com/get_qrcode/?service=https%3A%2F%2Fwww.toutiao.com%2F%3Fwid%3D1730548030059&need_logo=false&ui_version=3.2.1&aid=24&account_sdk_source=sso&sdk_version=2.2.5-beta.8&language=zh&verifyFp=verify_m303m6x5_RFowaRdd_mqcb_4vZy_8sQ8_Pzo6BfPsrvCR&fp=verify_m303m6x5_RFowaRdd_mqcb_4vZy_8sQ8_Pzo6BfPsrvCR"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json().get("data", {})
            self.token = data.get('token')
            qrcode = data.get('qrcode')
            
            if isinstance(qrcode, str):  # 确保 qrcode 是字符串
                print('base64 qrcode:', qrcode)
                qrcode_base64 = self.resize_qr_image(qrcode)
                if qrcode_base64:
                    # 使用 qrcode_terminal 打印二维码到命令行
                    qrcode_terminal.draw(qrcode_base64,)
                    print("请使用今日头条APP扫描上方二维码完成登录")
                else:
                    print("二维码处理失败。")
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
            elif data["status"] == "expired":
                print("二维码已过期，请重新生成。")
                return False
        return False

    def wait_for_login(self):
        print("正在等待扫码登录...")
        while True:
            if self.check_qr_status():
                break
            time.sleep(5)  # 每5秒检查一次
    def save_cookies(self):
        # 在此处保存用户的登录状态（比如 cookies）
        print("登录信息已保存。")

    def upload_video(self, file_path):
        # 处理视频上传逻辑
        print(f"正在上传视频文件 {file_path}...")
        # 在此添加上传 API 请求的逻辑