import requests
import json
import time
import os

SUNO_COOKIE = os.getenv('SUNO_COOKIE', '')

HEADERS = {
    'Cookie': SUNO_COOKIE,
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'Referer': 'https://suno.com/',
}

def generate_song(prompt, style="pop", title=""):
    try:
        # 1. Yangi trek yaratish
        create_url = 'https://studio-api.suno.ai/api/feed/v2/'
        payload = {
            'mv': 'chirp-v3-5',
            'prompt': prompt,
            'tags': style,
            'title': title if title else 'AI Song',
            'make_instrumental': False,
            'wait_audio': True
        }

        response = requests.post(create_url, headers=HEADERS, json=payload, timeout=60)

        if response.status_code != 200:
            return None, f"Suno API xatosi: {response.status_code}"

        data = response.json()
        clip_id = data.get('id')

        if not clip_id:
            return None, "Trek ID topilmadi"

        # 2. Tayyor bo'lishini kutish (max 120 soniya)
        for _ in range(24):
            time.sleep(5)
            status_url = f'https://studio-api.suno.ai/api/feed/v2/?ids={clip_id}'
            status_resp = requests.get(status_url, headers=HEADERS, timeout=30)

            if status_resp.status_code == 200:
                status_data = status_resp.json()
                clips = status_data.get('clips', [])
                if clips:
                    clip = clips[0]
                    if clip.get('status') == 'complete':
                        audio_url = clip.get('audio_url') or clip.get('video_url')
                        return audio_url, None
                    elif clip.get('status') == 'error':
                        return None, "Qo'shiq yaratishda xatolik"

        return None, "Vaqt tugadi, qo'shiq hali tayyor emas"

    except Exception as e:
        return None, f"Xatolik: {str(e)}"

def get_credits():
    try:
        url = 'https://studio-api.suno.ai/api/billing/credit/'
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return data.get('credits_left', 0)
        return 0
    except:
        return 0
