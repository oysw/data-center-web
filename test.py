import os

bsdir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
finaldir = os.path.join(bsdir, 'templates')
print(finaldir)

