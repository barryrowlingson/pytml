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
import pytmlargs
import hashlib


from bs4 import BeautifulSoup

import matplotlib
matplotlib.use("module://pytml.backend_autosave")

import backend_autosave as backend

import matplotlib.pyplot as plt

import os
import os.path

class Cache(object):
    """
    each cache entry stores:
      pre-execution context (pec)
      the code text
      the code output

    cache checking 
      if the code is different from the cached code, cache content is invalid
      if the pec is different from current context, cache content is invalid

    """

    def __init__(self, path, on=True):
        self.path = path
        self.on = on
        if not os.path.exists(path):
            os.makedirs(path)
    def get_cache(self, id, chunk):
        if not self.on:
            return (None, False)
        if not os.path.exists(os.path.join(self.path, id)):
            return (None, False)
        hexd = hashlib.md5()
        hexd.update(chunk)
        hexd = hexd.hexdigest()
        if os.path.exists(os.path.join(self.path, id, "input-%s" % hexd)):
            output = open(os.path.join(self.path, id, "output-%s" % hexd)).read()
            return (output, True)
        else:
            return (None, False)
    def create_cache_dir(self, id):
        entry_dir = os.path.join(self.path, id)
        if not os.path.exists(entry_dir):
            os.makedirs(entry_dir)
        pass
    def is_cache_valid(self, id):
        pass
    def update_cache_entry(self, id, input, output):
        self.create_cache_dir(id)
        entry_dir = os.path.join(self.path, id)
        hexd = hashlib.md5()
        hexd.update(input)
        hexd = hexd.hexdigest()
        input_file = os.path.join(entry_dir,"input-%s" % hexd)
        output_file = os.path.join(entry_dir,"output-%s" % hexd)
        with open(input_file,"w") as inputs:
            inputs.write(input)
        with open(output_file,"w") as outputs:
            outputs.write(output)
        pass

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

def code_not_asis(tag):
    if not tag.has_attr("class"):
        return False
    return tag.name=="code" and "language-python" in tag['class'] and "asis" not in tag['class']

class Codes():
    def __init__(self, filename, language, cache):
        self.lang = language
        self.soup = parseFile(filename)
        self.codes = self.soup.find_all(code_not_asis)
        ids = {}
        for code in self.codes:
            if not code.has_attr("id"):
                raise ValueError,"code section %s... has no id attribute" % str(code)[:40]
            if ids.has_key(code['id']):
                raise ValueError,"non-unique ids: %s " % code['id']
            ids[code['id']]=1
        self.chunkTexts = []
        self.env = {}
        self.text = StringIO.StringIO()
        self.cache = cache
        return None
        
#    def getCodes(self):
#        for code in self.codes:
#            self.chunkTexts.append(code.text)
#        return None

    def runCodes(self):
        self.chunkouts = []
        for code in self.codes:
            id = code['id']
            chunk = code.text
            (output, cached) = self.cache.get_cache(id, chunk)
            if not cached:
                if "expression" in code['class']:
                    output = expression(code)
                else:
                    output = block(code)
            else:
                code['class'].append("cached")
            self.chunkouts.append(output)
            self.cache.update_cache_entry(id, chunk, output)

    def replaceCodes(self):
        """ replace codes with output in the soup """
        for i in range(len(self.codes)):
            code = self.codes[i]
            if "hide" in code["class"]:
                code.decompose() # deletes the code tag from the soup
            else:
                # replace the contents with a stripped output
                t = self.chunkouts[i]
                t = t.strip()
                code.string = t
        
    
import argparse

def makeparser():
    parser = argparse.ArgumentParser() 
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
    parser.add_argument("--disable-cache",
                        help="dont get outputs from cache",
                        default=False,
                        action='store_true'
                        )
    parser.add_argument("--cachedir",
                        help="cache directory",
                        action=pytmlargs.writable_dir,
                        default="./cache/")
    parser.add_argument('--output', nargs='?',
                        type=argparse.FileType('w'),
                        default=sys.stdout,
                        help="output file")
    parser.add_argument("input_file", help="file to process")
                        
    return parser


def main():

    parser = makeparser()
    args = parser.parse_args()

    (dd,msgs) = pytmlargs.try_make_wdir(args.cachedir)
    if not dd:
        raise ValueError(msg)

    backend.setdpi = args.dpi
    backend.setfigsize = [args.width, args.height]
    backend.outdir = args.imgdir

    lang = "python"
    infile = args.input_file

    cache = Cache(args.cachedir, not args.disable_cache)

    codes = Codes(infile, lang, cache)
    codes.runCodes()
    codes.replaceCodes()
    args.output.write(codes.soup.prettify())

if __name__=="__main__":
    main()

