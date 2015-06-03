#!/usr/bin/env python

from ycmd.completers.nim.nimsuggest_completer import NimsuggestCompleter

def GetCompleter( user_options ):
  return NimsuggestCompleter( user_options )
