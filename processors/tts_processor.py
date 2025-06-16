# Chat gpt

import os
from typing import Dict, Any
import logging

from database.models import BrandKit
from services.minimax_tts import MinimaxTTS
from services.replicate_tts import ReplicateTTS
from database.functions import get_active_voice_over_api_key

logger = logging.getLogger(__name__)


class TTSProcessor:
    def __init__(self, brand_kit: BrandKit):
        self.brand_kit = brand_kit
        self.voice_config = brand_kit.voice
        self.tts_provider = MinimaxTTS(self.voice_config) if self.voice_config.provider == 'minimax' \
            else ReplicateTTS(self.voice_config)

    def generate_audio(self) -> str:
        """
        Generates audio from text using Minimax or Replicat services.

        """
        result_file = self.tts_provider.generate_audio(script=self.brand_kit.script_to_voice_over)
        return result_file
