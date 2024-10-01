## Setup on Windows 

First installation and set-up


1. Download the Jupyter Notebook from [Github](https://github.com/nvdsteen/mi-ctd-data-processing/archive/refs/heads/main.zip)
              
    [!NOTE]
    install in the directory of your choice; This is where you’ll start the notebook from.

2. Download SBEDataProcessing software and manual
   - Manual:  https://epic.awi.de/id/eprint/38965/1/SBEDataProcessing_7_23_2.pdf
   - Software: https://www.seabird.com/asset-get.download.jsa?code=251838 

3. Download **Python 3.12** https://www.python.org/downloads/windows/                                                                                                                 
   - install Python, **note the path**!
   - add path to environmental variable. Go to search bar, find environmental variable, click on `Path`, add a new variable with the path to the recently installed Python software.
   - Open the command line window and check python version: `python --version`

        [!NOTE]
        If python is not found: Disable Application aliases. Go to search bar, find App execution aliases, find the Python aliases and disable them.

                                                                    
4. Installation Notebook
    - Go to the notebook folder and activate the virtual environment: `Scripts\activate`
    - Install requirements: `pip install -Ur mi-ctd-data-processing\requirements.txt`
    - Install notebook: `pip install notebook`
    - Start Jupyter notebook: go to mi-ctd-data-processing and type: `jupyter notebook`

        [!NOTE]
        A new page will open in your web browser.

          
5. Creation of a batch file to start the notebook (including the virtual environment activation)
    - open Notepad, type:
        ```bat
        call path\to\activate\file
        cd path\to\notebook
        jupyter notebook
        ```
    - Save as `xxx.bat`

    - [!NOTE]
    To launch the notebook, just double click on the bat file.