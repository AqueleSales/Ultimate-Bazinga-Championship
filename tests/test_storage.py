from io import BytesIO
import pytest
from bazinga.storage import StorageNotConfigured, upload_media

class Upload:
    def __init__(self,data):
        self.stream=BytesIO(data)
        self.filename="art.png"
    def read(self,size=-1):
        return self.stream.read(size)

def test_upload_rejects_non_image_content(app):
    with app.app_context(),pytest.raises(ValueError):
        upload_media(Upload(b"not an image"))

def test_upload_rejects_files_over_limit(app):
    from bazinga.storage import MAX_UPLOAD_BYTES
    with app.app_context(),pytest.raises(ValueError,match="8 MB"):
        upload_media(Upload(b"\x89PNG\r\n\x1a\n"+b"x"*MAX_UPLOAD_BYTES))

def test_storage_requires_server_credentials(app):
    with app.app_context(),pytest.raises(StorageNotConfigured):
        upload_media(Upload(b"\x89PNG\r\n\x1a\ncontent"))

def test_external_image_urls_remain_compatible(app):
    from bazinga.storage import signed_media_url
    with app.app_context():
        assert signed_media_url("https://example.com/game.png")=="https://example.com/game.png"
