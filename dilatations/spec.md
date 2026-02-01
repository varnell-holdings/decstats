I want to write a python program.
Please look at claude.md and episodes.csv
Terminal based program.
"welcome to Dilatation Counter"
input year
input January-June or July-December

columns in episodes.csv of interest 'date' format DD-MM-YYY and 'upper'

we simply want to count the number of entries in 
'upper' with the value "30475"

At the end the program will out put to the terminal The number of dilatations performed in the period **** was - such and such.

Addition for new session: I now want the program to count the number of non empty entries in the 'upper' column as well and add this to the output with a line like 'The number of upper endoscopies performed in the period **** was - such and such.
Thanks

Session 3: Added OS-aware file path so the program works on both Windows and macOS. Used platform.system() to detect the OS — on Windows it reads episodes.csv from D:\John TILLET\episode_data\episodes.csv, on macOS it uses the relative path (current folder). Also attempted to set up a git remote for pushing to the decstats GitHub repo, but discovered dilatations is a subfolder of that repo, not its own repo. Will copy the updated file manually instead.
