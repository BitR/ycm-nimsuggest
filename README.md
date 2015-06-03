# ycm-nimsuggest
**A nimsuggest wrapper for YouCompleteMe**

This wrapper is currently at the prototype level and has quite a way to go, **use at your own risk**.

## Build and install nimsuggest
- Build Nim (See https://github.com/Araq/Nim)
- Build nimsuggest inside Nim/compiler/nimsuggest:
    `cd Nim/compiler/nimsuggest && nim c nimsuggest`
- Add the nimsuggest binary to your $PATH

## Vundle instructions:
- Make sure you have 'Valloric/YouCompleteMe' added to you Vundle plugin list. (See https://github.com/Valloric/YouCompleteMe).
- Clone this repo into the YouCompleteMe bundle:
    `git clone https://github.com/BitR/ycm-nimsuggest $HOME/.vim/bundle/YouCompleteMe/third_party/ycmd/ycmd/completers/nim`
