from rasa.core.channels.telegram import TelegramInput
from typing import Text

class TelegramInputChannel(TelegramInput):
    def get_metadata(self, request):
        metadata=request.json
        return metadata