"""
学习通防点名工具 - 主模块
自动监控课程中的签到/点名活动并自动提交，避免被点名后无响应。
"""

import hashlib
import time
import json
import re
import requests


# ------------------------------------------------------------------
# 常量
# ------------------------------------------------------------------
LOGIN_URL = "https://passport2.chaoxing.com/api/login"
COURSE_URL = "https://mooc1-api.chaoxing.com/mycourse/backclazzdata"
ACTIVE_LIST_URL = "https://mobilelearn.chaoxing.com/v2/apis/active/student/activelist"
PPT_SIGN_URL = "https://mobilelearn.chaoxing.com/pptSign/stuSignajax"
GENERAL_SIGN_URL = "https://mobilelearn.chaoxing.com/v2/apis/sign/signIn"

# 活动类型：type==2 表示签到活动
ACTIVITY_TYPE_SIGN_IN = 2

# 位置签到默认坐标（北京天安门广场，供无法获取真实坐标时使用）
DEFAULT_LATITUDE = "39.9042"
DEFAULT_LONGITUDE = "116.4074"
DEFAULT_ADDRESS = "中国"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 "
        "com.chaoxing.mobile/ChaoXingStudy_3_6.3.0_android_phone_906_74"
    ),
    "Content-Type": "application/x-www-form-urlencoded",
}

# 活动类型
SIGN_TYPES = {
    2: "普通签到",
    3: "手势签到",
    4: "位置签到",
    5: "二维码签到",
}


# ------------------------------------------------------------------
# 登录
# ------------------------------------------------------------------
def _md5(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()


def login(phone: str, password: str) -> requests.Session:
    """使用手机号和密码登录学习通，返回携带 Cookie 的 Session。"""
    session = requests.Session()
    session.headers.update(HEADERS)

    payload = {
        "uname": phone,
        "password": _md5(password),
        "rememberMe": "true",
        "fid": "-1",
        "t": "true",
    }

    resp = session.post(LOGIN_URL, data=payload, timeout=15)
    resp.raise_for_status()
    result = resp.json()

    if not result.get("status"):
        msg = result.get("msg2") or result.get("msg") or "登录失败"
        raise RuntimeError(f"登录失败：{msg}")

    print(f"[✓] 登录成功，欢迎 {result.get('realname', phone)}")
    return session


# ------------------------------------------------------------------
# 获取课程列表
# ------------------------------------------------------------------
def get_courses(session: requests.Session) -> list[dict]:
    """返回所有课程的基本信息列表，每项包含 courseId 和 classId。"""
    resp = session.get(COURSE_URL, params={"courseType": 1, "courseFolderId": 0}, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if not isinstance(data, dict):
        print("[!] 课程列表接口返回格式异常")
        return []

    courses = []
    for item in data.get("channelList", []):
        content = item.get("content") or {}
        course = {
            "name": content.get("name", "未知课程"),
            "courseId": str(content.get("id", "")),
            "classId": str(item.get("key", "")),
            "teacherName": content.get("teacherfactor", ""),
        }
        if course["courseId"] and course["classId"]:
            courses.append(course)

    print(f"[✓] 共获取到 {len(courses)} 门课程")
    return courses


# ------------------------------------------------------------------
# 查询活跃活动（签到/点名）
# ------------------------------------------------------------------
def get_active_list(session: requests.Session, course_id: str, class_id: str) -> list[dict]:
    """返回指定课程中当前活跃的活动列表。"""
    params = {
        "fid": "0",
        "courseId": course_id,
        "classId": class_id,
        "_": int(time.time() * 1000),
    }
    try:
        resp = session.get(ACTIVE_LIST_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result") == 1:
            return data.get("data", {}).get("activeList", [])
    except Exception as exc:
        print(f"  [!] 查询活动失败：{exc}")
    return []


# ------------------------------------------------------------------
# 签到：普通签到 / 手势签到
# ------------------------------------------------------------------
def _sign_normal(session: requests.Session, active_id: str, uid: str) -> str:
    """提交普通/手势签到，返回服务器消息。"""
    params = {
        "activeId": active_id,
        "uid": uid,
        "clientip": "",
        "latitude": "-1",
        "longitude": "-1",
        "appType": "15",
        "fid": "0",
        "name": "",
    }
    resp = session.get(PPT_SIGN_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.text.strip()


# ------------------------------------------------------------------
# 签到：位置签到（使用学校/上次已知位置的默认坐标）
# ------------------------------------------------------------------
def _sign_location(session: requests.Session, active_id: str, uid: str,
                   latitude: str = DEFAULT_LATITUDE, longitude: str = DEFAULT_LONGITUDE,
                   address: str = DEFAULT_ADDRESS) -> str:
    """提交位置签到，返回服务器消息。"""
    params = {
        "activeId": active_id,
        "uid": uid,
        "clientip": "",
        "latitude": latitude,
        "longitude": longitude,
        "address": address,
        "appType": "15",
        "fid": "0",
        "name": "",
    }
    resp = session.get(PPT_SIGN_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.text.strip()


# ------------------------------------------------------------------
# 签到：二维码签到（需要 enc 参数，此处仅占位，实际需手动输入）
# ------------------------------------------------------------------
def _sign_qrcode(session: requests.Session, active_id: str, uid: str, enc: str) -> str:
    """提交二维码签到，enc 为从二维码中提取的加密字符串。"""
    params = {
        "activeId": active_id,
        "enc": enc,
        "uid": uid,
        "clientip": "",
        "latitude": "-1",
        "longitude": "-1",
        "appType": "15",
        "fid": "0",
        "name": "",
    }
    resp = session.get(PPT_SIGN_URL, params=params, timeout=10)
    resp.raise_for_status()
    return resp.text.strip()


# ------------------------------------------------------------------
# 解析并处理单个活动
# ------------------------------------------------------------------
def _get_uid(session: requests.Session) -> str:
    """从 Session Cookie 中提取用户 UID。"""
    for cookie in session.cookies:
        if cookie.name == "_uid":
            return cookie.value
    return ""


def handle_activity(session: requests.Session, activity: dict, uid: str,
                    location_config: dict | None = None) -> None:
    """
    检测活动类型并自动签到/应答，从而避免被点名后无响应记录。

    目前支持：
      - 普通签到（type=2）
      - 手势签到（type=3）
      - 位置签到（type=4）
      - 二维码签到（type=5，仅输出提示，无法自动完成）
    """
    active_id = str(activity.get("id", ""))
    # otherId 区分签到子类型：2=普通, 3=手势, 4=位置, 5=二维码
    sign_type = activity.get("otherId", 0)
    status = activity.get("status", 0)      # 1=进行中, 2=已结束
    attend_info = activity.get("attendInfo", {}) or {}

    # 跳过已结束活动
    if status != 1:
        return

    # 跳过已签到活动
    if attend_info.get("status") == 1:
        return

    type_name = SIGN_TYPES.get(sign_type, f"未知类型({sign_type})")
    print(f"  [!] 发现活跃签到活动 [{type_name}] activeId={active_id}")

    try:
        if sign_type in (2, 3):
            msg = _sign_normal(session, active_id, uid)
        elif sign_type == 4:
            lat = str(location_config.get("latitude", DEFAULT_LATITUDE)) if location_config else DEFAULT_LATITUDE
            lon = str(location_config.get("longitude", DEFAULT_LONGITUDE)) if location_config else DEFAULT_LONGITUDE
            addr = location_config.get("address", DEFAULT_ADDRESS) if location_config else DEFAULT_ADDRESS
            msg = _sign_location(session, active_id, uid, lat, lon, addr)
        elif sign_type == 5:
            print("  [~] 二维码签到需要手动扫码，请打开学习通完成签到。")
            return
        else:
            print(f"  [~] 暂不支持自动处理 {type_name}，请手动操作。")
            return

        # 优先尝试解析 JSON 判断结果，兼容纯文本响应
        success = False
        try:
            parsed = json.loads(msg)
            success = str(parsed.get("result", "")) == "1" or parsed.get("status") is True
        except (json.JSONDecodeError, AttributeError):
            success = "success" in msg.lower()

        if success:
            print(f"  [✓] 签到成功！服务器返回：{msg}")
        else:
            print(f"  [?] 服务器返回：{msg}")
    except Exception as exc:
        print(f"  [✗] 签到请求出错：{exc}")


# ------------------------------------------------------------------
# 主监控循环
# ------------------------------------------------------------------
def monitor(phone: str, password: str, interval: int = 30,
            course_filter: list[str] | None = None,
            location_config: dict | None = None) -> None:
    """
    登录后持续监控所有课程中的签到/点名活动并自动应答。

    参数
    ----
    phone          : 手机号
    password       : 密码（明文，内部自动 MD5）
    interval       : 轮询间隔（秒），默认 30
    course_filter  : 只监控指定课程名称列表，为空则监控全部
    location_config: 位置签到坐标，格式 {"latitude": ..., "longitude": ..., "address": ...}
    """
    session = login(phone, password)
    uid = _get_uid(session)
    if not uid:
        raise RuntimeError("无法获取用户 UID，请检查登录状态")

    courses = get_courses(session)
    if course_filter:
        courses = [c for c in courses if c["name"] in course_filter]
        print(f"[✓] 过滤后监控 {len(courses)} 门课程：{[c['name'] for c in courses]}")

    if not courses:
        print("[!] 没有可监控的课程，退出。")
        return

    print(f"[✓] 开始监控，轮询间隔 {interval} 秒，按 Ctrl+C 退出\n")

    try:
        while True:
            for course in courses:
                activities = get_active_list(session, course["courseId"], course["classId"])
                sign_activities = [a for a in activities if a.get("type") == ACTIVITY_TYPE_SIGN_IN]
                for act in sign_activities:
                    handle_activity(session, act, uid, location_config)
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n[✓] 已停止监控。")


# ------------------------------------------------------------------
# 入口：读取 config.json 并启动
# ------------------------------------------------------------------
if __name__ == "__main__":
    import sys
    import os

    config_path = os.path.join(os.path.dirname(__file__), "config.json")
    if not os.path.exists(config_path):
        print("[!] 未找到配置文件，请先复制 config.example.json 为 config.json 并填写手机号和密码。")
        sys.exit(1)

    with open(config_path, encoding="utf-8") as f:
        cfg = json.load(f)

    if not cfg.get("phone") or not cfg.get("password"):
        print("[!] config.json 中 'phone' 和 'password' 字段不能为空。")
        sys.exit(1)

    monitor(
        phone=cfg["phone"],
        password=cfg["password"],
        interval=cfg.get("interval", 30),
        course_filter=cfg.get("courses") or None,
        location_config=cfg.get("location"),
    )
