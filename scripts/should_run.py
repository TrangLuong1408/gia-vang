"""Quyết định lượt chạy theo lịch (cron 5 phút) có cần lấy giá hay bỏ qua, dựa vào config.json."""
import json, os
from datetime import datetime
from zoneinfo import ZoneInfo

WINDOW = 15  # phút, bằng chu kỳ cron
DEFAULT = [{"from": "09:00", "to": "10:00", "step": 10, "on": True},
           {"from": "15:00", "to": "16:00", "step": 10, "on": True}]

def to_min(t):
    h, m = t.split(":")
    return int(h) * 60 + int(m)

def load_slots():
    try:
        slots = json.load(open("config.json", encoding="utf-8"))["slots"]
        if not isinstance(slots, list):
            raise ValueError("slots không phải danh sách")
        return slots
    except Exception as e:
        print("Không đọc được config.json, dùng lịch mặc định:", e)
        return DEFAULT

def is_due(slots, now):
    """now = số phút từ 00:00 (giờ Việt Nam). Đúng khi vừa qua một mốc chạy trong vòng WINDOW phút."""
    for s in slots:
        try:
            if not s.get("on", True):
                continue
            a, b, st = to_min(s["from"]), to_min(s["to"]), int(s["step"])
            if st <= 0 or b < a or now < a:
                continue
            t = a + min((now - a) // st, (b - a) // st) * st   # mốc chạy gần nhất
            if now - t < WINDOW:
                return True
        except Exception:
            continue
    return False

def main():
    if os.environ.get("GITHUB_EVENT_NAME", "") != "schedule":
        run, why = True, "chạy tay (bỏ qua lịch)"
    else:
        n = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh"))
        run = is_due(load_slots(), n.hour * 60 + n.minute)
        why = "%02d:%02d giờ VN, %s" % (n.hour, n.minute, "đến mốc chạy" if run else "chưa đến mốc")
    print("run =", run, "|", why)
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write("run=%s\n" % ("true" if run else "false"))

if __name__ == "__main__":
    main()
