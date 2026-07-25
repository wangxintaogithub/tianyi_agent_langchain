"""
腾讯云 COS (对象存储) 文件上传

前置条件：
  1. 开通腾讯云 COS 服务并创建存储桶
  2. 获取 API 密钥 (SecretId / SecretKey)
  3. 配置环境变量:
     - TENCENT_COS_SECRET_ID
     - TENCENT_COS_SECRET_KEY
     - TENCENT_COS_REGION
     - TENCENT_COS_BUCKET
"""
import io
import os
from typing import BinaryIO, Optional
from urllib.parse import quote


def upload_file(
    file: BinaryIO,
    filename: str,
    folder: str = "uploads",
    secret_id: Optional[str] = None,
    secret_key: Optional[str] = None,
    region: Optional[str] = None,
    bucket: Optional[str] = None,
) -> dict:
    """上传文件到腾讯云 COS

    Args:
        file: 文件二进制流
        filename: 文件名（用于 COS 存储路径）
        folder: COS 中的文件夹路径
        secret_id / secret_key / region / bucket: 不传则从 config 读取

    Returns:
        {
            "status": "ok" | "error",
            "cos_url": "https://...",
            "cos_key": "uploads/xxx.pdf",
            "error": "错误信息" (仅失败时)
        }
    """
    if secret_id is None:
        secret_id = os.environ.get("TENCENT_COS_SECRET_ID", "")
        secret_key = os.environ.get("TENCENT_COS_SECRET_KEY", "")
        region = os.environ.get("TENCENT_COS_REGION", "ap-guangzhou")
        bucket = os.environ.get("TENCENT_COS_BUCKET", "")

    if not all([secret_id, secret_key, region, bucket]):
        return {
            "status": "error",
            "error": "请配置完整腾讯云 COS 信息 (SecretId/SecretKey/Region/Bucket)",
        }

    try:
        from qcloud_cos import CosConfig, CosS3Client

        config = CosConfig(
            Region=region,
            SecretId=secret_id,
            SecretKey=secret_key,
            Token=None,
            Scheme="https",
        )
        client = CosS3Client(config)

        # 生成 COS 存储路径: uploads/年-月/文件名_时间戳.后缀
        import datetime
        today = datetime.date.today().strftime("%Y-%m")
        timestamp = datetime.datetime.now().strftime("%H%M%S")
        name, ext = os.path.splitext(filename)
        cos_key = f"{folder}/{today}/{name}_{timestamp}{ext}"

        # 读取文件内容
        file.seek(0)
        data = file.read()

        # 上传
        response = client.put_object(
            Bucket=bucket,
            Body=io.BytesIO(data),
            Key=cos_key,
            ContentType=_guess_mime(ext),
        )

        if response.get("ETag"):
            # 构造访问 URL
            encoded_key = quote(cos_key, safe="!/")
            cos_url = f"https://{bucket}.cos.{region}.myqcloud.com/{encoded_key}"

            return {
                "status": "ok",
                "cos_url": cos_url,
                "cos_key": cos_key,
                "etag": response.get("ETag"),
                "size": len(data),
            }
        else:
            return {"status": "error", "error": f"上传失败: {response}"}

    except ImportError:
        return {
            "status": "error",
            "error": "需要安装 cos-python-sdk-v5: pip install cos-python-sdk-v5",
        }
    except Exception as e:
        return {"status": "error", "error": f"COS 上传异常: {e}"}


def _guess_mime(ext: str) -> str:
    """根据扩展名猜测 MIME 类型"""
    mime_map = {
        ".pdf": "application/pdf",
        ".doc": "application/msword",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        ".xls": "application/vnd.ms-excel",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".csv": "text/csv",
        ".txt": "text/plain",
        ".md": "text/markdown",
        ".json": "application/json",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".zip": "application/zip",
    }
    return mime_map.get(ext.lower(), "application/octet-stream")
