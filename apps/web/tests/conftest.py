import os
import tempfile

os.environ.setdefault("SESSION_SECRET", "test-secret")
os.environ.setdefault("WEB_COOKIE_SECURE", "false")
os.environ.setdefault("ECO_CAPTURE_HOST", "mic.test")
# Never touch the real data/rev_babel.db - that's a live database, not a
# fixture, once the app is actually being used for a lesson.
os.environ.setdefault("DATA_DIR", tempfile.mkdtemp(prefix="rev-babel-test-"))
