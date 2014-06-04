import argparse
import os

def try_make_wdir(d):
    if not os.path.exists(d):
        os.mkdir(d)
    if not os.path.isdir(d):
        return (None, "path %s is not a directory" % d)
    if os.access(d,os.W_OK):
        return (d, "ok")
    else:
        return (None, "path %s is not writable" % d)

class writable_dir(argparse.Action):
    def __call__(self, parse, namespace, values, option_string=None):
        d = values

        (dd, msg) = try_make_wdir(d)
        if not dd:
            raise argparse.ArgumentError(self, msg)
        else:
            setattr(namespace, self.dest, dd)

class readable_dir(argparse.Action):
    def __call__(self,parser, namespace, values, option_string=None):
        prospective_dir=values
        if not os.path.isdir(prospective_dir):
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a valid path".format(prospective_dir))
        if os.access(prospective_dir, os.R_OK):
            setattr(namespace,self.dest,prospective_dir)
        else:
            raise argparse.ArgumentTypeError("readable_dir:{0} is not a readable dir".format(prospective_dir))

