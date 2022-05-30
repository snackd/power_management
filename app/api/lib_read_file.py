from .. import db
import magic #python magic bin


ALLOWED_EXTENSIONS = {'json'}
ALLOWED_MIME_TYPES = {'application/json', 'text/plain'}

def is_allowed_file(file):
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
    else:
        return False

    mime_type = magic.from_buffer(file.stream.read(), mime=True)
    if (
        mime_type in ALLOWED_MIME_TYPES and
        ext in ALLOWED_EXTENSIONS
    ):
        # move the cursor to the beginning
        file.stream.seek(0,0)
        return True

    return False

