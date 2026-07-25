"""
企业微信机器人通知 - 通过 Webhook 发送消息到微信群

使用方式：
  1. 在企业微信群中添加"群机器人"
  2. 复制 Webhook 地址
  3. 配置到环境变量 WECHAT_WEBHOOK_URL
"""
import json
from typing import Optional
from urllib import request as urllib_request
from urllib.error import URLError


def send_text(
    content: str,
    webhook_url: Optional[str] = None,
    mentioned_list: Optional[list[str]] = None,
) -> dict:
    """发送文本消息到企业微信群

    Args:
        content: 消息内容（最长 2048 字节）
        webhook_url: Webhook 地址，不传则从 config 读取
        mentioned_list: 需要 @ 的成员 userid 列表，["@all"] 表示所有人

    Returns:
        API 响应 dict
    """
    if webhook_url is None:
        import os
        webhook_url = os.environ.get("WECHAT_WEBHOOK_URL", "")

    if not webhook_url:
        return {"errcode": -1, "errmsg": "未配置 WECHAT_WEBHOOK_URL"}

    payload = {
        "msgtype": "text",
        "text": {
            "content": content[:2048],  # 微信限制 2048 字节
        },
    }
    if mentioned_list:
        payload["text"]["mentioned_list"] = mentioned_list

    return _post(webhook_url, payload)


def send_markdown(
    content: str,
    webhook_url: Optional[str] = None,
) -> dict:
    """发送 Markdown 消息到企业微信群（支持标题、表格、引用等）"""
    if webhook_url is None:
        import os
        webhook_url = os.environ.get("WECHAT_WEBHOOK_URL", "")

    if not webhook_url:
        return {"errcode": -1, "errmsg": "未配置 WECHAT_WEBHOOK_URL"}

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "content": content[:4096],  # Markdown 限制 4096 字节
        },
    }
    return _post(webhook_url, payload)


def send_file_result_summary(
    results: list[dict],
    webhook_url: Optional[str] = None,
) -> dict:
    """发送文件处理结果汇总到微信群"""
    success = [r for r in results if r["status"] == "ok"]
    failed = [r for r in results if r["status"] == "error"]

    lines = [
        "📎 **文件处理报告**\n",
        f"> 共处理 {len(results)} 个文件"
    ]

    if success:
        lines.append(f"> ✅ 成功: {len(success)} 个")
        for s in success[:5]:  # 最多显示 5 个
            lines.append(f">    - [{s['filename']}]({s.get('cos_url', '#')})")
        if len(success) > 5:
            lines.append(f">    ... 还有 {len(success) - 5} 个")

    if failed:
        lines.append(f"\n> ❌ 失败: {len(failed)} 个")
        for f in failed:
            lines.append(f">    - {f['filename']}: {f.get('error', '未知错误')}")

    # 前 200 字符的内容摘要
    if success:
        first = success[0]
        content = first.get("content", "")
        if content and len(content) > 200:
            lines.append(f"\n📝 文件内容预览（前 200 字）:\n> {content[:200]}...")

    return send_markdown("\n".join(lines), webhook_url)


def _post(url: str, payload: dict) -> dict:
    """发送 POST 请求"""
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib_request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib_request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except URLError as e:
        return {"errcode": -1, "errmsg": f"请求失败: {e.reason}"}
    except Exception as e:
        return {"errcode": -1, "errmsg": str(e)}
