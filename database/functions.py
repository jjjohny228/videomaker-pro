from database.models import AssemblyAiApiKey, VoiceOverApiKey
from typing import Literal

def get_active_assembly_ai_api_key():
    assemblyai_object = AssemblyAiApiKey.get_or_none(is_active=True)
    if assemblyai_object:
        return assemblyai_object.api_key
    else:
        raise ValueError('No active assembly ai api key found')


def get_active_voice_over_api_key(provider: Literal['minimax', 'replicate']) -> VoiceOverApiKey:
    voice_over_object = VoiceOverApiKey.get_or_none(provider=provider, is_active=True)
    if voice_over_object:
        return voice_over_object
    else:
        raise ValueError(f'No active api key for the {provider} provider')
