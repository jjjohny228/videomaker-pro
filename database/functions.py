from database.models import AssemblyAiApiKey

def get_active_assembly_ai_api_key():
    assemblyai_object = AssemblyAiApiKey.get_or_none(is_active=True)
    if assemblyai_object:
        return assemblyai_object.api_key
    else:
        raise ValueError('No active assembly ai api key found')
