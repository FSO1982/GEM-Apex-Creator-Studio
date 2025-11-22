import os
import sys
import tempfile
import unittest
from types import SimpleNamespace

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "src"))

from exporters.markdown_exporter import MarkdownExporter
from gui.sidebar import SidebarController
from gui.state import AppState
from models.character import Character


class DummyAIClient:
    def configure(self, *_args, **_kwargs):
        return None


class DummyFileDialog:
    def __init__(self, paths):
        self.paths = paths

    def askopenfilenames(self, *_, **__):
        return self.paths


class SidebarControllerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state = AppState(
            ai_client=DummyAIClient(),
            character=Character(),
            exporter=MarkdownExporter(
                output_dir=os.path.join(self.temp_dir.name, "output")
            ),
        )
        self.state.saved_dossiers_dir = os.path.join(self.temp_dir.name, "saved")
        self.state.ensure_directories()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_upload_image_adds_new_files(self):
        controller = SidebarController(
            self.state,
            filedialog_module=DummyFileDialog(["a.png", "b.png", "a.png"]),
            messagebox_module=SimpleNamespace(showwarning=lambda *_, **__: None),
        )
        added = controller.upload_image()
        self.assertEqual(set(added), {"a.png", "b.png"})
        self.assertEqual(len(self.state.uploaded_images), 2)

    def test_save_dossier_writes_file(self):
        controller = SidebarController(
            self.state,
            filedialog_module=DummyFileDialog([]),
            messagebox_module=SimpleNamespace(
                showwarning=lambda *_, **__: None, showinfo=lambda *_, **__: None
            ),
        )
        path = controller.save_dossier("Test User")
        self.assertTrue(os.path.exists(path))
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertIn("Test User", content)


if __name__ == "__main__":
    unittest.main()
