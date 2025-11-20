import unittest
from auth_mi import (
    get_access_token,
    call_version_api,
    call_whoami_api,
    call_experiment_api,
    run_zebra_ai_client
)

class TestAuthMI(unittest.TestCase):
    def test_access_token(self):
        token = get_access_token()
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 0)

    def test_version_api(self):
        token = get_access_token()
        version_info = call_version_api(token)
        self.assertIsInstance(version_info, dict)
        self.assertIn("version", version_info)

    def test_whoami_api(self):
        token = get_access_token()
        whoami_info = call_whoami_api(token)
        self.assertIsInstance(whoami_info, dict)
        self.assertTrue("user" in whoami_info or "name" in whoami_info)

    def test_experiment_api(self):
        token = get_access_token()
        result = call_experiment_api(token)
        self.assertIsInstance(result, dict)
        self.assertIn("questions", result)
        self.assertIsInstance(result["questions"], list)

    def test_run_zebra_ai_client(self):
        result = run_zebra_ai_client()
        self.assertIsInstance(result, dict)
        self.assertIn("questions", result)
        self.assertIsInstance(result["questions"], list)

if __name__ == "__main__":
    result = run_zebra_ai_client()
    print("Extracted Questions:")
    for q in result:
        print("-", q)