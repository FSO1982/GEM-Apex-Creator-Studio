import os
import sys
import tempfile
import unittest

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from exporters.markdown_exporter import MarkdownExporter
from gui.state import AppState
from gui.tabs.chat import ChatController
from models.character import Character


class DummyResponse:
    def __init__(self, text):
        self.text = text


class DummyChatSession:
    def __init__(self):
        self.messages = []

    def send_message(self, message):
        self.messages.append(message)
        return DummyResponse(f"echo:{message}")


class DummyAIClient:
    def __init__(self):
        self.configured_with = None
        self.started_with = None

    def configure(self, key):
        self.configured_with = key

    def start_chat(self, prompt):
        self.started_with = prompt
        return DummyChatSession()


class ChatControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state = AppState(
            ai_client=DummyAIClient(),
            character=Character(),
            exporter=MarkdownExporter(
                output_dir=os.path.join(self.temp_dir.name, "out")
            ),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_start_simulation_configures_and_starts_chat(self):
        controller = ChatController(self.state)
        prompt = controller.start_simulation(
            "Nova", 28, {"Trait": "Calm"}, "writer-key"
        )
        self.assertIsNotNone(prompt)
        self.assertIn("Nova", prompt)
        self.assertIsNotNone(self.state.chat_session)
        self.assertEqual(self.state.ai_client.configured_with, "writer-key")
        self.assertIn("Calm", self.state.ai_client.started_with)

    def test_send_message_returns_response_text(self):
        controller = ChatController(self.state)
        controller.start_simulation("Nova", 28, {}, "writer-key")
        response = controller.send_message("hi", "Nova")
        self.assertEqual(response, "echo:hi")


if __name__ == "__main__":
    unittest.main()
