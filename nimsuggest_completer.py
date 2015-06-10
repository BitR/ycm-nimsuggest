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

def warning(msg):
    log(logging.WARNING, msg)

def info(msg):
    log(logging.INFO, msg)

def debug(msg):
    log(logging.DEBUG, msg)

COMPLETION_TIMEOUT=2

class NimsuggestCompleter(Completer):
    def __init__(self, user_options):
        super(NimsuggestCompleter, self).__init__(user_options)
        self._popener = utils.SafePopen
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
        _logger = logging.getLogger(__name__)
        proc = None
        self._dataqueue = Queue()
        try:
            info('Starting %s' % self._binary)
            self._proc = proc = self._popener([self._binary] + args, executable = self._binary, stdin = PIPE, stdout = PIPE, stderr = PIPE, shell=True)
            info('Started %s' % self._binary)
        except:
            error(traceback.format_exc())
            return

        try:
            while not proc.poll():
                data = proc.stdout.readline()
                self._dataqueue.put(data)
        except:
            error(traceback.format_exc())
        finally:
            if proc.returncode != None and proc.returncode != 0:
                error('[Queue] Nimsuggest retcode %d: %s' % (proc.returncode, data))

    def OnFileReadyToParse(self, request_data):
        if hasattr(self, '_proc') and self._proc != None:
            if self._proc.poll():
                warning('[ReadyToParse] Nimsuggest has exited with code %s' % str(self._proc.returncode))
            return

        filepath = request_data['filepath']
        args = ['--stdin', filepath]

        self._StartProc(args)

    def _StartProc(self, args):
        self._args = args

        self._readthread = Thread(target=self._RunProc, args=[args])
        self._readthread.daemon = True
        self._readthread.start()

    def _ReadResult(self):
        output = ''
        while True:
            try:
                d = self._dataqueue.get(timeout=COMPLETION_TIMEOUT)
                if '> sug' in d:
                    output = ''
                    continue
                # Find marker
                if d.startswith('> '):
                    break
                output += d
            except Empty:
                if not self._proc.poll():
                    warning('[Read] Nimsuggest has exited with code %d' % self._proc.returncode)
                else:
                    self._proc.kill()
                self._StartProc(self._args)
                break
        return output

    def _Cmd(self, data):
        if not hasattr(self, '_proc') or self._proc == None:
            # Seems the thread isn't quite ready yet
            warning("_proc isn't ready yet")
            return ''

        try:
            self._proc.stdin.write(data)
            # Add marker ('> ')
            self._proc.stdin.write('\n')
            self._proc.stdin.flush()
            output = self._ReadResult()
            return output
        except IOError as e:
            warning('[Cmd] Nimsuggest has exited')
            self._proc = None
            self._StartProc(self._args)

        return ''

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
                detailed_info = '%s: %s\n%s' %
                    (name, typeName, comment.strip('"').replace('\\x0A', '\n') if comment != '""' else ''))
