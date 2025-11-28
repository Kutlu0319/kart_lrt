import requests
import re
import time
from typing import List, Dict, Any

class CatCastM3UGenerator:
    def __init__(self):
        self.base_url = "https://api.catcast.tv/api/channels?page={}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://catcast.tv/',
            'Origin': 'https://catcast.tv'
        })

    def fetch_page(self, page: int) -> List[Dict[str, Any]]:
        url = self.base_url.format(page)
        for attempt in range(3):
            try:
                r = self.session.get(url, timeout=30)
                r.raise_for_status()
                data = r.json()
                if data.get("status") == 1:
                    return data["data"]["list"]["data"]
                else:
                    print(f"⚠ Sayfa {page} geçersiz yanıt: {data.get('status')}")
                    return []
            except Exception as e:
                print(f"Sayfa {page} hatası ({attempt+1}/3): {e}")
                time.sleep(5)
        return []

    def fetch_real_stream(self, shortname: str) -> str | None:
        url = f"https://catcast.tv/channel/{shortname}"
        for attempt in range(3):
            try:
                r = self.session.get(url, timeout=30, headers={
                    'User-Agent': 'Mozilla/5.0',
                    'Referer': 'https://catcast.tv/',
                    'Origin': 'https://catcast.tv'
                })
                if r.status_code != 200:
                    time.sleep(5)
                    continue
                match = re.search(r'https.*?\.m3u8[^"]*', r.text)
                if match:
                    return match.group(0)
            except Exception as e:
                print(f"{shortname} stream alınamadı ({attempt+1}/3): {e}")
                time.sleep(5)
        return None

    def is_valid_channel(self, ch: Dict[str, Any]) -> bool:
        return all(ch.get(field) for field in ['id', 'name', 'shortname'])

    def generate_m3u_content(self, channels: List[Dict[str, Any]], page: int) -> str:
        content = ""
        for ch in channels:
            if not self.is_valid_channel(ch):
                continue
            stream = self.fetch_real_stream(ch['shortname'])
            if not stream:
                print(f"⚠ Stream yok: {ch['shortname']}")
                continue
            content += f'#EXTINF:-1 tvg-id="{ch["id"]}" tvg-name="{ch["name"]}" tvg-logo="{ch["logo"]}" group-title="Sayfa {page}",{ch["name"]}\n'
            content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0\n'
            content += f'#EXTVLCOPT:http-referer=https://catcast.tv/\n'
            content += f'{stream}\n'
            time.sleep(0.3)
        return content

    def generate_playlist(self):
        pages = list(range(1, 4))  # CI test için küçük aralık
        m3u = "#EXTM3U\n"
        total = 0
        for page in pages:
            channels = self.fetch_page(page)
            if channels:
                m3u += self.generate_m3u_content(channels, page)
                total += len(channels)
            time.sleep(1)
        with open("catcast_tv.m3u", "w", encoding="utf-8") as f:
            f.write(m3u)
        print(f"✅ M3U oluşturuldu! Toplam kanal (geçerli): {total}")


if __name__ == "__main__":
    CatCastM3UGenerator().generate_playlist()
