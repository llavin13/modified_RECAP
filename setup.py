from distutils.core import setup
import py2exe
import sys

#"C:\\Program Files (x86)\\Microsoft Visual Studio 9.0\\VC\\redist\\x86\\Microsoft.VC90.CRT"
#"C:\\Anaconda\\Lib\\site-packages\\numpy\\core"

sys.setrecursionlimit(5000)

includes = ['scipy.special._ufuncs_cxx',
            'scipy.sparse.csgraph._validation']

setup(console=['main.py'],options={"py2exe":{"includes": includes}})

