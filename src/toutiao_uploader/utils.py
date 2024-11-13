import hashlib
import hmac
from datetime import datetime,timezone
import cv2


def generate_x_amz_date() -> str:
    """
    生成 x-amz-date 的值
    :return: 当前时间的 AWS 标准格式，例如：20241111T115209Z
    """
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")



def generate_authorization(ak: str, sk: str, canonical_request: str) -> str:
    """
    生成 Authorization 头部的值
    :param ak: Access Key
    :param sk: Secret Key
    :param canonical_request: 规范化请求字符串
    :return: Authorization 头部的值
    """
    # Step 1: Create a string to sign
    region = "cn-north-1"
    service = "vod"
    now = datetime.now(timezone.utc)  # 使用时区感知的 UTC 时间
    date = now.strftime("%Y%m%d")
    scope = f"{date}/{region}/{service}/aws4_request"
    hashed_request = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    string_to_sign = (
        f"AWS4-HMAC-SHA256\n{generate_x_amz_date()}\n{scope}\n{hashed_request}"
    )

    # Step 2: Calculate the signing key
    def sign(key, msg):
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    k_date = sign(f"AWS4{sk}".encode("utf-8"), date)
    k_region = sign(k_date, region)
    k_service = sign(k_region, service)
    k_signing = sign(k_service, "aws4_request")
    signature = hmac.new(k_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

    # Step 3: Construct Authorization header
    signed_headers = "x-amz-content-sha256;x-amz-date;x-amz-security-token"
    return (
        f"AWS4-HMAC-SHA256 Credential={ak}/{scope}, "
        f"SignedHeaders={signed_headers}, Signature={signature}"
    )


def is_expired(timestamp):
    """
    判断时间戳是否过期，支持 ExpiredTime 和 expire_time_str 格式。
    
    参数:
    - timestamp (str): ISO 格式的时间戳（UTC 或含时区信息）。
    
    返回:
    - bool: True 表示已过期，False 表示未过期。
    """
    try:
        # 如果时间戳以 "Z" 结尾，表示是 UTC 时间
        if timestamp.endswith("Z"):
            expiration_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        else:
            # 含时区偏移的时间戳，直接解析
            expiration_time = datetime.fromisoformat(timestamp)
        
        # 当前 UTC 时间
        current_time = datetime.now(timezone.utc)
        
        # 比较是否过期
        return current_time > expiration_time
    except Exception as e:
        print(f"Error parsing timestamp '{timestamp}': {e}")
        return True  # 如果解析失败，认为已过期


def get_video_dimensions(video_path):
    # 使用 OpenCV 读取视频
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"无法打开视频文件: {video_path}")
    # 获取视频的宽度和高度
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    return width, height