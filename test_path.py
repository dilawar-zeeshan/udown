import os
def resolve_script_path(*ps):
    return os.path.abspath(os.path.join(*ps))

script_path = ['/home/zee/Desktop/downloader/pot-server/server/src/generate_once.ts']
# In yt-dlp, configuration_arg returns a list if multiple were passed, or the first element.
# The code does: "[0]". So it got the string:
s = '/home/zee/Desktop/downloader/pot-server/server/src/generate_once.ts'
print(resolve_script_path(s, os.pardir, os.pardir))
