#!/usr/bin/env python

import os
from Queue import Queue
from nose.tools import eq_, raises
from ycmd.completers.nim.nimsuggest_completer import NimsuggestCompleter
from ycmd.request_wrap import RequestWrap
from ycmd import user_options_store

TEST_DIR = os.path.dirname( os.path.abspath( __file__ ) )
DATA_DIR = os.path.join( TEST_DIR, 'testdata' )
PATH_TO_TEST_FILE = os.path.join( DATA_DIR, 'test.nim' )
# Use test file as dummy binary
DUMMY_BINARY = '/tmp/nimsuggest_bin'
PATH_TO_MEMBERS_RES = os.path.join( DATA_DIR, 'nimsuggest_output_members.txt' )

REQUEST_DATA = {
  'filepath' : PATH_TO_TEST_FILE,
  'file_data' : { PATH_TO_TEST_FILE : { 'filetypes' : [ 'nim' ] } }
}

class NimsuggestCompleter_test( object ):
  def setUp( self ):
    user_options = user_options_store.DefaultOptions()
    self._completer = NimsuggestCompleter( user_options )
    self._completer._StartProc = self._StartProc

  def _StartProc(self, args):
    self._completer._args = args
    self._completer._RunProc(args)

  def _BuildRequest( self, line_num, column_num ):
    request = REQUEST_DATA.copy()
    request[ 'column_num' ] = column_num
    request[ 'line_num' ] = line_num
    with open( PATH_TO_TEST_FILE, 'r') as testfile:
      request[ 'file_data' ][ PATH_TO_TEST_FILE ][ 'contents' ] = (
        testfile.read() )
    return RequestWrap( request )

#  def FindNimsuggestBinary_test( self ):
#    user_options = user_options_store.DefaultOptions()
#
#    eq_( None,
#         self._completer._binary )

  # Test line-col to offset in the file after a unicode occurrences.
  def ComputeCandidatesInner_test( self ):
    self._completer._binary = DUMMY_BINARY
    with open( PATH_TO_MEMBERS_RES, 'r' ) as nimsugoutput:
      mock = MockPopen( returncode=0, stdout=nimsugoutput.read(), stderr='' )
    self._completer._popener = mock
    request = self._BuildRequest(4, 3)
    self._completer.OnFileReadyToParse(request)
    result = self._completer.ComputeCandidatesInner(request)[0:1]

    eq_( result, [ {
        'menu_text': 'abs (system.abs)', 
        'insertion_text': 'abs', 
        'kind': 'proc (x: int): int{.noSideEffect, gcsafe, locks: 0.}',
        'extra_menu_info': 'skProc',
        'detailed_info': 'abs: proc (x: int): int{.noSideEffect, gcsafe, locks: 0.}\n'}
      ] )

  def OnFileReadyToParse_test( self ):
    self._completer._binary = DUMMY_BINARY
    with open( PATH_TO_MEMBERS_RES, 'r' ) as nimsugoutput:
      mock = MockPopen( returncode=0, stdout=nimsugoutput.read(), stderr='' )
    self._completer._popener = mock
    request = self._BuildRequest(4, 3)
    self._completer.OnFileReadyToParse(request)
    eq_( mock.cmd, [ DUMMY_BINARY, '--stdin', PATH_TO_TEST_FILE ] )

  def ProcShutsdown_test( self ):
    self._completer._binary = DUMMY_BINARY
    with open( PATH_TO_MEMBERS_RES, 'r' ) as nimsugoutput:
      mock = MockPopen( returncode=0, stdout=nimsugoutput.read(), stderr='' )
    self._completer._popener = mock
    request = self._BuildRequest(4, 3)
    self._completer.OnFileReadyToParse(request)
    oldproc = self._completer._proc

    oldproc.kill()

    self._completer._dataqueue = Queue()
    self._completer.ComputeCandidatesInner(request)
    result = self._completer.ComputeCandidatesInner(request)[0:1]
    assert len(result) > 0
    

class MockPipe(object):
  def __init__(self, contents=None):
    self.data = ''
    if contents:
      self.lines = contents.splitlines()
    self.line = 0

  def readline(self):
    if not self.hasdata():
      return None

    self.line += 1
    return self.lines[self.line - 1] + '\n'

  def write(self, data):
    self.data += data

  def flush(self):
    pass

  def hasdata(self):
    return self.line < len(self.lines)

class MockSubprocess( object ):
  def __init__( self, returncode, stdout, stderr ):
    self.returncode = returncode
    self.stdout = MockPipe(stdout)
    self.stderr = MockPipe(stderr)
    self.stdin = MockPipe()

  def communicate( self, stdin ):
    self.stdin = stdin
    return ( self.stdout, self.stderr )

  def poll(self):
    if self.returncode or self.stdout.hasdata():
      return None
    self.returncode = 42
    return self.returncode

  def kill(self):
    self.returncode = -1

class MockPopen( object ):
  def __init__( self, returncode=None, stdout=None, stderr=None ):
    self._returncode = returncode
    self._stdout = stdout
    self._stderr = stderr
    self.cmd = None
    self.executable = None

  def __call__( self, cmd, executable = None, stdout=None, stderr=None, stdin=None, shell=None ):
    self.cmd = cmd
    self.executable = executable
    return MockSubprocess( self._returncode, self._stdout, self._stderr )
