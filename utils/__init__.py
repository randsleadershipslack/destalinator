import codecs

def get_local_file_content(file_name):
    """Read the contents of `file_name` into a unicode string, return the unicode string."""
    f = codecs.open(file_name, encoding='utf-8')
    ret = f.read().strip()
    f.close()
    return ret
