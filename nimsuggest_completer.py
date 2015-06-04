#!/usr/bin/env python

import os
import sys
import io
import tempfile
import logging
import itertools
import time
import traceback
from threading import Thread
from Queue import Queue, Empty

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

COMPLETION_TIMEOUT=0.05
BOOT_TIMEOUT=2

class NimsuggestCompleter(Completer):
    def __init__(self, user_options):
        super(NimsuggestCompleter, self).__init__(user_options)
        self._binary = utils.PathToFirstExistingExecutable(['nimsuggest'])
        self._dataqueue = Queue()

        if not self._binary:
            msg = "Couldn't find nimsuggest binary. Is it in the path?"
            error(msg)
            raise RuntimeError(msg)

        info('Nimsuggest completer loaded')

    def SupportedFiletypes(self):
        return set(['nim'])

    def _RunProc(self, args):
        try:
            self._proc = Popen([self._binary] + args, executable = self._binary, stdin = PIPE, stdout = PIPE, stderr = PIPE, shell=True)
        except:
            error(traceback.format_exc())
            return

        try:
            while not self._proc.poll():
                data = self._proc.stdout.readline()
                self._dataqueue.put(data)
        finally:
            if self._proc.returncode != None and self._proc.returncode != 0:
                error('Nimsuggest retcode %d: %s' % (self._proc.returncode, data))
                return []

            try:
                self._proc.stdin.write('quit\n')
                self._proc.stdin.flush()
            except:
                pass

    def OnFileReadyToParse(self, request_data):
        filepath = request_data['filepath']
        args = ['--stdin', filepath]

        if hasattr(self, '_proc'):
            if not self._proc.poll():
                warning('Nimsuggest has exited with code %d' % self._proc.returncode)
                return
        self._readthread = Thread(target=self._RunProc, args=[args])
        self._readthread.daemon = True
        self._readthread.start()

    def _Cmd(self, data):
        if not hasattr(self, '_proc'):
            # Seems the thread isn't quite ready yet
            return ''
        self._proc.stdin.write(data)
        self._proc.stdin.flush()
        output = ''
        found_cmd = False
        while True:
            try:
                d = self._dataqueue.get(timeout=(COMPLETION_TIMEOUT if found_cmd else BOOT_TIMEOUT))
                if data in d:
                    output = ''
                    found_cmd = True
                    continue
                output += d
            except Empty:
                break
        return output

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
        dirtyfile = None
        if contents:
            dirtyfile = tempfile.mkstemp()[1]
            open(dirtyfile, 'w').write(contents)
        cmd = 'sug %s%s:%d:%d\n' % (filename, ';' + 
                dirtyfile if dirtyfile else '', linenum, column)
        try:
            data = self._Cmd(cmd)

            return [self._CreateCompletionData(line,
                        contents.splitlines()[linenum-1] if contents and len(contents) >= linenum - 1 else None)
                    for line in data.splitlines()
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
    tmpfile = tempfile.mkstemp('.nim')[1]
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
        compl.OnFileReadyToParse(request_data)
        time.sleep(.5)
        compl.ComputeCandidatesInner(request_data)
        compl.ComputeCandidatesInner(request_data)
    finally:
        os.unlink(tmpfile)
