import base64
from hashlib import md5


def file_md5(file_content: str) -> tuple[bytes, str]:
    file_binary = base64.b64decode(file_content)
    return file_binary, md5(file_binary).hexdigest()
