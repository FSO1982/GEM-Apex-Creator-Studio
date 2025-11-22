import json
import os
import tempfile
import unittest

from utils.config_loader import (
    load_api_keys,
    sanitize_key,
    validate_google_api_key,
)


class ConfigLoaderTests(unittest.TestCase):
    def test_sanitize_key_strips_whitespace(self):
        self.assertEqual(sanitize_key("  abc  \n"), "abc")
        self.assertEqual(sanitize_key(None), "")

    def test_validate_google_api_key_accepts_expected_shape(self):
        valid_key = "AIza" + ("x" * 30)
        self.assertEqual(validate_google_api_key(valid_key), (True, ""))

        too_short_key = "AIza123"
        self.assertFalse(validate_google_api_key(too_short_key)[0])
        self.assertFalse(validate_google_api_key(" ")[0])

    def test_load_api_keys_merges_sources_with_precedence(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_path = os.path.join(tmp_dir, "config.json")
            env_path = os.path.join(tmp_dir, ".env")

            config_writer = "AIzaCONFIG" + ("a" * 22)
            env_writer = "AIzaENVFILE" + ("b" * 20)
            runtime_writer = "AIzaRUNTIME" + ("c" * 19)

            with open(config_path, "w", encoding="utf-8") as cfg:
                json.dump({"writer_key": config_writer, "vision_key": "via_config"}, cfg)

            with open(env_path, "w", encoding="utf-8") as env_file:
                env_file.write(f"GOOGLE_API_KEY={env_writer}\n")
                env_file.write("GOOGLE_IMAGEN_API_KEY=AIzaIMGFILEbbbbbbbbbbbbbbbbbbbbbb\n")

            original_env = os.environ.copy()
            os.environ["GOOGLE_API_KEY"] = runtime_writer
            os.environ["GOOGLE_VISION_API_KEY"] = "AIzaRUNTIMEVISION" + ("d" * 12)

            try:
                keys = load_api_keys(config_path=config_path, env_path=env_path)
            finally:
                os.environ.clear()
                os.environ.update(original_env)

            self.assertEqual(keys["writer_key"], runtime_writer)
            self.assertEqual(keys["vision_key"], "AIzaRUNTIMEVISION" + ("d" * 12))
            self.assertEqual(keys["image_key"], "AIzaIMGFILEbbbbbbbbbbbbbbbbbbbbbb")


if __name__ == "__main__":
    unittest.main()
