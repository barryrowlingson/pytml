#!/bin/env python
#
# extract python code from <pre><code> block
#
from test.test_support import captured_stdout, captured_output, \
     captured_stderr, captured_stdin
     
import StringIO
import sys
import code
import os.path

from bs4 import BeautifulSoup

import matplotlib
matplotlib.use("module://pytml.backend_autosave")

import backend_autosave as backend

import matplotlib.pyplot as plt

def resetplot(code):
    """ called before a chunk is run """
    if "data-size" in code.attrs.keys():
        sizes = [int(s) for s in code.attrs["data-size"].split(",")]
        backend.setfigsize = sizes
        plt.figure(figsize=sizes)
    else:
        if backend.setfigsize:
            plt.figure(figsize=backend.setfigsize)
    
    if "data-dpi" in code.attrs.keys():
        backend.setdpi = int(code.attrs['data-dpi'])

    if "data-outdir" in code.attrs.keys():
        od = code.attrs['data-outdir']
        if not os.path.exists(od):
            raise IOError("No such folder %s " % os.path.abspath(od))
        backend.outdir = od

    template = "%s-%%s.png" % code['id']
    backend.filename_template = template
    backend.plotnumber = 0

def parseFile(filename):
    soup = BeautifulSoup(file(filename))
    return soup

import code

class RedirectStdStreams(object):
    def __init__(self, stdout=None, stderr=None):
        self._stdout = stdout or sys.stdout
        self._stderr = stderr or sys.stderr

    def __enter__(self):
        self.old_stdout, self.old_stderr = sys.stdout, sys.stderr
        self.old_stdout.flush(); self.old_stderr.flush()
        sys.stdout, sys.stderr = self._stdout, self._stderr

    def __exit__(self, exc_type, exc_value, traceback):
        self._stdout.flush(); self._stderr.flush()
        sys.stdout = self.old_stdout
        sys.stderr = self.old_stderr

context = {}

def expression(code):
    global context
    s = str(eval(code.text, context))
    return s

def block(code):
    chunk = code.text
    if chunk.startswith("\n"):
        chunk = chunk[1:]
    if 'id' in code.attrs.keys():
        resetplot(code)
    s1 = StringIO.StringIO()
    with RedirectStdStreams(stdout=s1, stderr=s1):
        show(chunk)
    return s1.getvalue()
    

def show(input):

    lines = iter(input.splitlines())
    
    def readline(prompt):
        try:
            command = next(lines)
        except StopIteration:
            raise EOFError()
        print prompt, command
        return command

    global context
    code.interact(readfunc=readline, local=context, banner="")


class Codes():
    def __init__(self, filename, language):
        self.lang = language
        self.soup = parseFile(filename)
        self.codes = self.soup.find_all("code", "language-%s" % self.lang)
        self.chunkTexts = []
        self.env = {}
        self.text = StringIO.StringIO()
        return None
        
    def getCodes(self):
        for code in self.codes:
            self.chunkTexts.append(code.text)
        return None

    def runCodes(self):
        self.chunkouts = []
        for code in self.codes:
            chunk = code.text
            if "expression" in code['class']:
                output = expression(code)
            else:
                output = block(code)
            self.chunkouts.append(output)
        
    def replaceCodes(self):
        for i in range(len(self.codes)):
            code = self.codes[i]
            if "hide" in code["class"]:
                code.decompose()
            else:
                t = self.chunkouts[i]
                t = t.strip()
                code.string = t
        
    
import argparse

def makeparser():
    parser = argparse.ArgumentParser() 
    parser.add_argument("input_file", help="file to process")
    parser.add_argument("--imgdir",
                        help="image directory",
                        type=str,
                        default="./")
    parser.add_argument("--dpi", 
                        help="image dpi",
                        type=int,
                        default=100)
    parser.add_argument("--width",
                        help="figure width (inches)",
                        type=int,
                        default=4)
    parser.add_argument("--height",
                        help="figure height (inches)",
                        type=int,
                        default=3)
    return parser


def main():

    parser = makeparser()
    args = parser.parse_args()

    backend.setdpi = args.dpi
    backend.setfigsize = [args.width, args.height]
    backend.outdir = args.imgdir

    lang = "python"
    infile = sys.argv[1]
    codes = Codes(infile, lang)
    codes.runCodes()
    codes.replaceCodes()
    print codes.soup.prettify()

    
if __name__=="__main__":
    main()

