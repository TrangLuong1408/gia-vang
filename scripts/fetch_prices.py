"""Lấy giá bán ra / mua vào và ghi thêm một dòng vào data.json nếu giá hoặc giờ cập nhật có thay đổi."""
import json, re, sys
from datetime import datetime
from zoneinfo import ZoneInfo
import requests
from bs4 import BeautifulSoup

UA = {"User-Agent": "Mozilla/5.0 (compatible; gia-vang-bot/1.0)"}
num = lambda t: int(re.sub(r"[^\d]", "", t) or 0)

def get(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

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
    soup = get("https://baotinmanhhai.vn/bang-gia-vang")
    for c in rows(soup):
        if c[0].strip().lower() == "kim gia bảo 24k" and len(c) >= 4:
            m = re.search(r"Cập nhật lúc\s*\d{4}-\d{2}-\d{2}\s*(\d{2}:\d{2})", soup.get_text(" "))
            chg = 0
            if len(c) >= 5 and re.search(r"\d", c[4]):
                chg = num(c[4]) // 1000 * (-1 if c[4].strip().startswith("-") else 1)
            return {"buy": num(c[2]), "sell": num(c[3]), "t": m.group(1) if m else "", "chg": chg}
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
