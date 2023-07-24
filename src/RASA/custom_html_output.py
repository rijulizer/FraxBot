from typing import Text, Dict, Any
from rasa.core.channels import OutputChannel, UserMessage

class CustomHTMLOutput(OutputChannel):
    @classmethod
    def name(cls) -> Text:
        return "custom_html"

    def send_text_message(
        self, recipient_id: Text, message: Text, **kwargs: Any
    ) -> None:
        # Assuming the `message` contains the HTML text to display
        # You can add any additional processing or sanitization if needed

        # Create a UserMessage object with the formatted HTML text
        user_message = UserMessage(
            text=message,
            output_channel=self.name(),
            sender_id=recipient_id,
            parse_data=None,
            input_channel=None,
        )

        # Send the UserMessage using the dispatcher
        dispatcher = kwargs.get("dispatcher")
        if dispatcher:
            dispatcher.utter_message(user_message)
