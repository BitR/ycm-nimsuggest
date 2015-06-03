#!/usr/bin/env python

import os
import tempfile
import logging
import itertools

from subprocess import Popen, PIPE
from ycmd.completers.completer import Completer
from ycmd import responses
from ycmd import utils

_logger = logging.getLogger(__name__)

class NimsuggestCompleter(Completer):
    def __init__(self, user_options):
        super(NimsuggestCompleter, self).__init__(user_options)
        self._binary = utils.PathToFirstExistingExecutable(['nimsuggest'])

        if not self._binary:
            msg = "Couldn't find nimsuggest binary. Is it in the path?"
            _logger.error(msg)
            raise RuntimeError(msg)

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

            return [self._CreateCompletionData(line,
                        contents.splitlines()[linenum] if contents and len(contents) >= linenum else None)
                    for line in list(itertools.dropwhile(
                        lambda l: not l.startswith('>'), data.splitlines()))[1:]
                    if line.startswith('sug')]
        except KeyboardInterrupt:
            pass
        finally:
            if dirtyfile:
                os.unlink(dirtyfile)

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
                detailed_info = comment.strip('"').replace('\\x0A', '\n') if comment != '""' else ' ')
                
