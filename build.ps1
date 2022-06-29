function Get-Dependencies {
    pip install matplotlib pillow  # pillow is required for image processing, matplotlib for timeseries plotting
    pip install sv-ttk  # sv-ttk is required for modern look and feel
    pip install requests pyquery lxml  # requests is required for scraping, pyquery and lxml is required for parsing
    pip install pyyaml pyinstaller  # pyyaml is required for yaml parsing, pyinstaller is required for packaging
    pip install dateutils appdirs # dateutils is required for date handling (e.g., get UTC timestamps), appdirs is required for app data storage cross-platform
    pip install gender_guesser # gender_guessor for email template filling
}

function Start-Build {
    pyinstaller --onefile -w `
        --add-data "C:\Users\Cao20\AppData\Local\Programs\Python\Python310\tcl\winico;tcl\winico" `
        --add-data "C:\Users\Cao20\work\SchoolUtils\Lib\site-packages\sv_ttk;sv_ttk" `
        --add-data ".\src\grade_checker\assets;grade_checker\\assets" `
        --add-data ".\Lib\site-packages\gender_guesser;gender_guesser" `
        --icon ".\src\grade_checker\assets\icon.ico" `
        --hidden-import "sv_ttk" `
        --upx-dir ".\Scripts\upx" `
        --noconfirm .\src\main.py
}

Start-Build