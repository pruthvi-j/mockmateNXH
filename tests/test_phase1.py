"""
NextHire - Stage 1 Phase 1 Verification Suite
Tests project architecture, routes, static asset delivery, and JARVIS state endpoints.
"""
import unittest
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app import create_app
from backend.config import Config

class Phase1TestSuite(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True
        cls.client = cls.app.test_client()

    def test_health_endpoint(self):
        """Test the core /api/health endpoint."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["status"], "online")
        self.assertIn("NextHire", data["system"])
        self.assertIn("Stage 1 - Phase 1", data["stage"])

    def test_jarvis_state_endpoint(self):
        """Test the JARVIS assistant metadata endpoint."""
        response = self.client.get("/api/jarvis/state")
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["assistant"], "JARVIS")
        for state in ["IDLE", "LISTENING", "THINKING", "SPEAKING", "PROCESSING"]:
            self.assertIn(state, data["supported_states"])

    def test_frontend_routes_served(self):
        """Verify all Phase 1 frontend interfaces return HTTP 200."""
        routes = [
            "/",
            "/login",
            "/register",
            "/dashboard",
            "/interview",
            "/feedback",
            "/history"
        ]
        for route in routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 200, f"Failed to serve {route}")
                self.assertIn("NextHire", response.get_data(as_text=True))

    def test_jarvis_interface_content(self):
        """Verify the interview page contains core JARVIS visual elements and states."""
        response = self.client.get("/interview")
        self.assertEqual(response.status_code, 200)
        content = response.get_data(as_text=True)

        # Verify key JARVIS HUD components
        self.assertIn("jarvis-arc-core", content)
        self.assertIn("jarvis-ring-outer", content)
        self.assertIn("jarvis-ring-middle", content)
        self.assertIn("jarvisWaveCanvas", content)
        self.assertIn("liveTranscript", content)
        self.assertIn("micToggleBtn", content)
        self.assertIn("state-switcher-hud", content)

    def test_static_assets_delivered(self):
        """Verify CSS and JS assets are reachable and non-empty."""
        assets = [
            "/css/style.css",
            "/css/jarvis.css",
            "/js/main.js",
            "/js/jarvis.js"
        ]
        for asset in assets:
            with self.subTest(asset=asset):
                response = self.client.get(asset)
                self.assertEqual(response.status_code, 200, f"Failed to load asset {asset}")
                self.assertGreater(len(response.data), 100, f"Asset {asset} is unexpectedly empty")

    def test_uploads_directory_configured(self):
        """Verify upload folder exists."""
        self.assertTrue(Config.UPLOAD_FOLDER.exists())

if __name__ == "__main__":
    unittest.main()
