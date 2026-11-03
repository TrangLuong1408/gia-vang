"""Lấy giá bán ra / mua vào và ghi thêm một dòng vào data.json nếu giá hoặc giờ cập nhật có thay đổi."""
import json, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (compatible; gia-vang-bot/1.0)"}
num = lambda t: int(re.sub(r"[^\d]", "", t) or 0)

def fetch(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    r.encoding = "utf-8"
    return r.text

def get(url):
    return BeautifulSoup(fetch(url), "html.parser")

def rows(soup):
    for tr in soup.find_all("tr"):
        cells = [c.get_text(" ", strip=True) for c in tr.find_all(["td", "th"])]
        if cells:
            yield cells

def knp():
    soup = get("https://kimnganphuc.vn/")
    for c in rows(soup):
        if "nhẫn ép vỉ kim ngân phúc" in c[0].lower() and len(c) >= 3:
            m = re.search(r"Cập nhật\s*(?:lúc)?\s*(\d{1,2}:\d{2})", soup.get_text(" "))
            return {"buy": num(c[1]), "sell": num(c[2]), "t": m.group(1).zfill(5) if m else ""}
    raise RuntimeError("Không tìm thấy dòng Nhẫn ép vỉ Kim Ngân Phúc")

def kgb():
    html = fetch("https://baotinmanhhai.vn/bang-gia-vang")
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for i, l in enumerate(lines):
        if l.lower() == "kim gia bảo 24k":
            nums = []
            for x in lines[i + 1:i + 8]:
                if re.fullmatch(r"[+-]?[\d.,]+", x):
                    nums.append(x)
                elif nums:
                    break
            if nums and re.fullmatch(r"\d{2}\.\d{1,2}", nums[0]):
                nums = nums[1:]          # bỏ cột hàm lượng (99.99)
            if len(nums) >= 2:
                chg = 0
                if len(nums) >= 3:
                    chg = num(nums[2]) // 1000 * (-1 if nums[2].startswith("-") else 1)
                m = re.search(r"Cập nhật lúc\s*\d{4}-\d{2}-\d{2}\s*(\d{2}:\d{2})", text)
                return {"buy": num(nums[0]), "sell": num(nums[1]), "t": m.group(1) if m else "", "chg": chg}
    print("DEBUG: độ dài HTML =", len(html), "| có 'Kim Gia' =", "Kim Gia" in html, "| số dòng chữ =", len(lines))
    i = html.find("Kim Gia")
    print("DEBUG: đoạn quanh 'Kim Gia':", html[max(0, i - 100):i + 300] if i >= 0 else "(không có)")
    raise RuntimeError("Không tìm thấy dòng Kim Gia Bảo 24K")

def main():
    new = {"date": datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%d/%m/%Y"), "knp": knp(), "kgb": kgb()}
    for k in ("knp", "kgb"):
        if not new[k]["buy"] or not new[k]["sell"]:
            raise RuntimeError("Giá trống: " + k)
    log = json.load(open("data.json", encoding="utf-8"))
    key = lambda e: (e["knp"]["buy"], e["knp"]["sell"], e["knp"]["t"], e["kgb"]["buy"], e["kgb"]["sell"], e["kgb"]["t"])
    if log and key(log[0]) == key(new):
        print("Không có thay đổi"); return
    log.insert(0, new)
    json.dump(log[:400], open("data.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("Đã thêm:", new)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("LỖI:", e); sys.exit(1)
