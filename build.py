import zipfile
from os import walk, path

filelist = []
for (dirpath, dirnames, filenames) in walk(path.dirname(path.realpath(__file__))):
    filelist.extend(filenames)
    break

print(filelist)

with zipfile.ZipFile("build/AlexChat.pyw", "w") as archive:
	for filename in filelist:
		archive.write(filename)