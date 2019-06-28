# ycm-nimsuggest
**A nimsuggest wrapper for YouCompleteMe**
> Nim completion support for vim

Ycm-nimsuggest is a plugin for [YouCompleteMe](https://github.com/Valloric/YouCompleteMe) that adds completion support for the [Nim](https://github.com/nim-lang/Nim) programming language.

Requirements:
- [YouCompleteMe](https://github.com/Valloric/YouCompleteMe)
- Vim filetype [autocommand](#autocommand) for nim files

## Build and install nimsuggest
- Build [Nim](https://github.com/nim-lang/Nim) (includes nimsuggest) - v0.20.0 is currently recommended
- Make sure both the nim and nimsuggest binaries are in your $PATH

## Vundle instructions:
- Make sure you have [YouCompleteMe](https://github.com/Valloric/YouCompleteMe) added to you Vundle plugin list
- Install YouCompleteMe with python3 (python3 ./install.py)
- Clone this repo into the YouCompleteMe bundle:

        git clone https://github.com/BitR/ycm-nimsuggest \
        $HOME/.vim/bundle/YouCompleteMe/third_party/ycmd/ycmd/completers/nim

## Autocommand
Make sure to have an autocommand for .nim files ([nimrod.vim](https://github.com/zah/nimrod.vim) provides this one):

    au BufNewFile,BufRead *.nim set filetype=nim
