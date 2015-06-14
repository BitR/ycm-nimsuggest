# ycm-nimsuggest
**A nimsuggest wrapper for YouCompleteMe**
> Nim completion support for vim

Ycm-nimsuggest is a plugin for [YouCompleteMe](https://github.com/Valloric/YouCompleteMe) that adds completion support for the [Nim](https://github.com/nim-lang/Nim) programming language.

Requirements:
- [YouCompleteMe](https://github.com/Valloric/YouCompleteMe)
- Vim filetype [autocommand](#autocommand) for nim files

## Build and install nimsuggest
- Build [Nim](https://github.com/nim-lang/Nim) - v0.11.2 is currently recommended
- Build nimsuggest inside Nim/compiler/nimsuggest:

        cd Nim/compiler/nimsuggest && nim c -d:release nimsuggest

- Copy the nimsuggest binary to the same directory as your nim binary, to ensure they both handle compilation paths the same way
- Make sure both binaries are in your $PATH

**Note**: Nimsuggest has moved to [nim-lang/nimsuggest](https://github.com/nim-lang/nimsuggest), however that version will only build with the unstable devel branch of [Nim](https://github.com/nim-lang/Nim) for now.

## Vundle instructions:
- Make sure you have [YouCompleteMe](https://github.com/Valloric/YouCompleteMe) added to you Vundle plugin list
- Clone this repo into the YouCompleteMe bundle:

        git clone https://github.com/BitR/ycm-nimsuggest \
        $HOME/.vim/bundle/YouCompleteMe/third_party/ycmd/ycmd/completers/nim

## Autocommand
Make sure to have an autocommand for .nim files ([nimrod.vim](https://github.com/zah/nimrod.vim) provides this one):

    au BufNewFile,BufRead *.nim set filetype=nim
