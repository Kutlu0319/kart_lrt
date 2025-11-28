import requests
import json
import time
import re
from typing import List, Dict, Any

class CatCastM3UGenerator:
    def __init__(self):
        self.base_url = "https://api.catcast.tv/api/channels?page={}"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': 'https://catcast.tv/'
        })

    def fetch_page(self, page_num: int) -> List[Dict[str, Any]]:
        url = self.base_url.format(page_num)
        try:
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            data = response.json()

            if data.get("status") == 1:
                return data["data"]["list"]["data"]

        except Exception as e:
            print("Sayfa çekilirken hata:", e)

        return []

    def fetch_real_stream(self, shortname: str) -> str | None:
        """
        Kanal HTML sayfasından gerçek .m3u8 linkini çeker
        """
        try:
            url = f"https://catcast.tv/channel/{shortname}"
            r = self.session.get(url, timeout=20)
            if r.status_code != 200:
                return None

            # JS içinde geçen gerçek m3u8 URL
            match = re.search(r'https.*?\.m3u8[^"]*', r.text)
            if match:
                return match.group(0)

        except Exception as e:
            print(f"Stream URL alınamadı ({shortname}):", e)

        return None

    def generate_m3u_content(self, channels: List[Dict[str, Any]], page_num: int) -> str:
        m3u_content = ""

        for channel in channels:
            if not self.is_valid_channel(channel):
                continue

            channel_id = channel.get('id', '')
            channel_name = channel.get('name', '').strip()
            channel_logo = channel.get('logo', '')
            shortname = channel.get('shortname', '').strip()

            # GERÇEK STREAM LİNKİ BURADA ÇEKİLİYOR
            real_stream_url = self.fetch_real_stream(shortname)
            if not real_stream_url:
                print(f"⚠ Stream bulunamadı → {shortname}")
                continue

            m3u_content += f'#EXTINF:-1 tvg-id="{channel_id}" tvg-name="{channel_name}" tvg-logo="{channel_logo}" group-title="Sayfa {page_num}",{channel_name}\n'
            m3u_content += f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n'
            m3u_content += f'#EXTVLCOPT:http-referer=https://catcast.tv/\n'
            m3u_content += f'{real_stream_url}\n'

            time.sleep(0.3)  # site engellemesin

        return m3u_content

    def is_valid_channel(self, channel: Dict[str, Any]) -> bool:
        required_fields = ['id', 'name', 'shortname']
        return all(field in channel and channel[field] for field in required_fields)

    def generate_playlist(self):
        pages = list(range(1, 51)) + [480, 481]

        all_m3u_content = "#EXTM3U\n"
        total_channels = 0

        for page_num in pages:
            channels = self.fetch_page(page_num)

            if channels:
                page_content = self.generate_m3u_content(channels, page_num)
                all_m3u_content += page_content
                total_channels += len(channels)

            time.sleep(1)

        with open('catcast_tv.m3u', 'w', encoding='utf-8') as f:
            f.write(all_m3u_content)

        print(f"🎉 M3U oluşturuldu! Toplam kanal (geçerli): {total_channels}")


def main():
    generator = CatCastM3UGenerator()
    generator.generate_playlist()


if __name__ == "__main__":
    main()
