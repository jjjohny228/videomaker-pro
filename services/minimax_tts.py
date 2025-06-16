import os
import time

import requests
import json
import logging
from mutagen import File as MutagenFile
from aiohttp.abc import HTTPException

from core.config import Config
from database.functions import get_active_voice_over_api_key

logger = logging.getLogger(__name__)


class MinimaxTTS:
    def __init__(self, voice_config):
        self.voice_config = voice_config
        self.temp_dir = Config.TEMP_FOLDER

    def generate_audio(self, script: str):
        """
        Voiceover script
        """
        output_file = f'{self.temp_dir}/{int(time.time())}_minimax_tts.mp3'
        active_api_key = get_active_voice_over_api_key('minimax')
        group_id = active_api_key.group_id
        voice_id = self.voice_config.voice_id
        speed = self.voice_config.speed
        api_key = active_api_key.api_key
        if len(script) > 200000:
            raise ValueError("Text is too long (max 200,000 characters).")
        url = f'https://api.minimaxi.chat/v1/t2a_v2?GroupId={group_id}'
        payload = {
            "model": "speech-02-turbo",
            "text": script,
            "stream": False,
            "voice_setting":{
                "voice_id":voice_id,
                "speed":speed,
                "vol":1,
                "pitch":0
            },
            "audio_setting": {
                "sample_rate": 32000,
                "bitrate": 128000,
                "format": "mp3",
                "channel": 1
            }
        }
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, json=payload)
        try:
            response.raise_for_status()
        except HTTPException as e:
            logger.error(f'Raised error during minimax voice over creation: {e}')

        resp_json = response.json()
        base_resp = resp_json.get("base_resp", {})
        status_code = base_resp.get("status_code")
        status_msg = base_resp.get("status_msg")
        if status_code not in (200, 0):
            logger.error(f"MiniMax API error: status_code={status_code}, status_msg={status_msg}")
            return

        parsed_json = json.loads(response.text)
        audio_value = bytes.fromhex(parsed_json['data']['audio'])
        if not audio_value:
            raise RuntimeError("No audio in response: %s" % response.text)
        with open(output_file, 'wb') as f:
            f.write(audio_value)
        return output_file

    def clone_voice(self, audio_path, group_id, api_key, voice_id):
        """
        Clones a voice based on the uploaded file.
        voice_id: minimum 8 characters, letters and numbers, starts with a letter.
        """

        custom_voice_file_id = self._upload_cloned_voice(audio_path, group_id, api_key)
        if len(voice_id) < 8 or not voice_id[0].isalpha() or not any(c.isdigit() for c in voice_id):
            raise ValueError("voice_id must be at least 8 chars, start with a letter, contain letters and numbers.")
        url = f"https://api.minimaxi.chat/v1/voice_clone?GroupId={group_id}"
        payload = json.dumps({
            "file_id": custom_voice_file_id,
            "voice_id": voice_id
        })
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        resp_json = response.json()
        if resp_json.get("base_resp", {}).get("status_code") != 0:
            raise RuntimeError("Voice clone failed: %s" % resp_json)
        return voice_id

    @staticmethod
    def _upload_cloned_voice(audio_path, group_id, api_key):
        """
        Uploads an audio file to MiniMax for voice cloning.
        Validation: MP3/M4A/WAV format, duration 10 sec - 5 min, size < 20MB.Clones the voice based on the uploaded file.
        voice_id: minimum 8 characters, letters and numbers, starts with a letter.
        """
        # Валидация файла
        allowed_ext = ('.mp3', '.m4a', '.wav')
        if not audio_path.lower().endswith(allowed_ext):
            raise ValueError("Audio file must be in MP3, M4A, or WAV format.")
        if os.path.getsize(audio_path) > 20 * 1024 * 1024:
            raise ValueError("Audio file must be less than 20MB.")

        try:
            audio_file = MutagenFile(audio_path)
            if audio_file is None:
                raise ValueError("Unable to read audio file metadata.")

            duration = audio_file.info.length
            if duration < 10:
                raise ValueError("Audio duration must be at least 10 seconds.")
            if duration > 300:  # 5 минут = 300 секунд
                raise ValueError("Audio duration must not exceed 5 minutes.")
        except Exception as e:
            if "duration" in str(e).lower():
                raise e
            else:
                raise ValueError(f"Unable to read audio file duration: {e}")

        url = f'https://api.minimaxi.chat/v1/files/upload?GroupId={group_id}'
        headers = {'Authorization': f'Bearer {api_key}'}
        data = {'purpose': 'voice_clone'}
        files = {'file': open(audio_path, 'rb')}
        response = requests.post(url, headers=headers, data=data, files=files)
        response.raise_for_status()
        file_id = response.json().get("file", {}).get("file_id")
        if not file_id:
            raise RuntimeError("File upload failed: %s" % response.text)
        return file_id
