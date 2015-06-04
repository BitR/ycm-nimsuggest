#!/usr/bin/env python

import os
import sys
import tempfile
import logging
import itertools

from subprocess import Popen, PIPE
from ycmd.completers.completer import Completer
from ycmd import responses
from ycmd import utils

_logger = logging.getLogger(__name__)

def log(level, msg):
    _logger.log(level, '[nimcompl] %s' % msg)

def error(msg):
    log(logging.ERROR, msg)

def info(msg):
    log(logging.INFO, msg)

def debug(msg):
    log(logging.DEBUG, msg)

class NimsuggestCompleter(Completer):
    def __init__(self, user_options):
        super(NimsuggestCompleter, self).__init__(user_options)
        self._binary = utils.PathToFirstExistingExecutable(['nimsuggest'])

        if not self._binary:
            msg = "Couldn't find nimsuggest binary. Is it in the path?"
            error(msg)
            raise RuntimeError(msg)

        info('Nimsuggest completer loaded')

    def SupportedFiletypes(self):
        return set(['nim'])

    def ShouldUseNowInner(self, request_data):
        return len(self.ComputeCandidatesInner(request_data)) > 0

    def ComputeCandidatesInner(self, request_data):
        filepath = request_data['filepath']
        linenum = request_data['line_num']
        colnum = request_data['column_num']
        contents = utils.ToUtf8IfNeeded(
            request_data['file_data'][filepath]['contents'])
        return self._Suggest(filepath, linenum, colnum, contents)

    def _Suggest(self, filename, linenum, column, contents):
        args = ['--stdin', filename]
        p = Popen(args, executable = self._binary, stdin = PIPE, stdout = PIPE, stderr = PIPE, shell=True)
        dirtyfile = None
        if contents:
            dirtyfile = tempfile.mkstemp()[1]
            open(dirtyfile, 'w').write(contents)
        cmd = 'sug %s%s:%d:%d\nquit\n' % (filename, ';' + 
                dirtyfile if dirtyfile else '', linenum, column)
        try:
            data, err = p.communicate(cmd)

            if p.returncode != 0:
                error('Nimsuggest retcode %d: %s' % (p.returncode, data))
                return []

            return [self._CreateCompletionData(line,
                        contents.splitlines()[linenum-1] if contents and len(contents) >= linenum - 1 else None)
                    for line in list(itertools.dropwhile(
                        lambda l: not l.startswith('>'), data.splitlines()))[1:]
                    if line.startswith('sug')]
        except KeyboardInterrupt:
            pass
        finally:
            if dirtyfile:
                os.unlink(dirtyfile)
        return []

    def _CreateCompletionData(self, line, contents):
        skType, name, typeName, filename, linenum, colnum, comment = line.split('\t')[1:]
        longname = name
        if '.' in name:
            name = name.split('.')[-1]
            longname = name + ' (' + longname + ')'

        return responses.BuildCompletionData(
                insertion_text = name,
                menu_text = longname,
                extra_menu_info = skType,
                kind = typeName,
                detailed_info = comment.strip('"').replace('\\x0A', '\n') if comment != '""' else None)
                
if __name__ == "__main__":
    compl = NimsuggestCompleter(
            {
                'min_num_of_chars_for_completion': 1,
                'auto_trigger': None
                })
    tmpfile = tempfile.mkstemp()[1]
    contents = """import math

a = open('/dev/zero', 'r')
a.
"""
    with open(tmpfile, 'w') as f:
        f.write(contents)

    try:
        request_data = {
            'filepath': tmpfile,
            'line_num': 4,
            'column_num': 3,
            'file_data': {
                tmpfile: {
                    'contents': contents
                }
            }
        }
        compl.ComputeCandidatesInner(request_data)
        compl.ComputeCandidatesInner(request_data)
        #print compl.ComputeCandidatesInner(request_data)
    finally:
        os.unlink(tmpfile)
