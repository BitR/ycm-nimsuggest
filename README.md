# ycm-nimsuggest
**A nimsuggest wrapper for YouCompleteMe**

This wrapper is currently at the prototype level and has quite a way to go, **use at your own risk**.

## Build and install nimsuggest
- Build [Nim](https://github.com/Araq/Nim)
- Build nimsuggest inside Nim/compiler/nimsuggest:

        cd Nim/compiler/nimsuggest && nim c nimsuggest

- Copy the nimsuggest binary to the same directory as your nim binary, to ensure they both handle compilation paths the same way
- Make sure both binaries are in your $PATH

## Vundle instructions:
- Make sure you have [Valloric/YouCompleteMe](https://github.com/Valloric/YouCompleteMe) added to you Vundle plugin list
- Clone this repo into the YouCompleteMe bundle:

        git clone https://github.com/BitR/ycm-nimsuggest \
        $HOME/.vim/bundle/YouCompleteMe/third_party/ycmd/ycmd/completers/nim

Make sure to have an autocommand for .nim files (faith/vim-go provides this one):

    au BufNewFile,BufRead *.nim set filetype=nim
