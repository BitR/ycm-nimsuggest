#!/usr/bin/env python3

from ycmd.completers.nim.nimsuggest_completer import NimsuggestCompleter

def GetCompleter( user_options ):
  return NimsuggestCompleter( user_options )
