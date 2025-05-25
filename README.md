<h1 align="center">PAJAMALAND Media PyRes</h1>
<p align="center"><img width="256" height="275" src="https://github.com/user-attachments/assets/c4af2b6a-7485-4693-a619-835023d64c84"> </p>
<p align="center">An easy-to-use <b>Python</b> program for converting videos to <b>Apple ProRes 422</b> using <b>FFmpeg</b>, to aid the video editing process.</p>
<p align="center">If you use <b>H.264/5</b> to edit video, it's going to <b>lag like fuck.</b> Converting your files into <b>ProRes</b> should fix this (somewhat)!</p>

## Requirements
Python 3  
FFmpeg installed into your PATH  
Pyside6

## Setup
### On Windows:
Download the PyRes.exe binary from the Releases section. Please ensure you have Python 3, FFmpeg and tkinterdnd2 installed already.

### On Linux & Mac:
> NOTE: When using pip on Linux, your distribution may not allow packages to be installed through it as it may manage Python packages externally. These instructions are "generic" and not for any specific distribution, so if you encounter an error following this method, please consult your distribution's support channels - there's some good workarounds on StackOverflow!

`pip install ffmpeg`   
`pip install pyside6`  
`git clone https://github/Pajamaland/PyRes`  
`python pyres.py`
## Usage
Run the script with `python pyres.py`, drag and drop or select your files/folders, choose your preset, and just go! That's it! Output will be labeled FILENAME_prores.mov in the same directory as the original file.

## Why not just use Shutter Encoder/Media Encoder/FFmpeg CLI?
While all these tools are great and awesome, we made PyRes because it's <b>quick and easy</b>, with just one function; <b>convert the video into ProRes.</b> Drag, click, done. PyRes is simple by design, and drastically improves workflow through its convenience. <br></br>
Much love to the Shutter Encoder guys though, we love your software!
