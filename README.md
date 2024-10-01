# mi-ctd-data-processing
This reposisory contains the Ireland's Marine Institute's CTD Data Processing functionality.

The main aim of this work was to create a consistent set of data processing steps that could be used both at sea, with limited internet access, and back in the office/laboratory. 

The Marine Institute uses 3 Jupyter Notebooks, written in python, to process CTD data from acqusition, conduct quality control checks and carry out calibration based on bottles collected concurrent to CTD measurements:
1. CTD Profiles Processing: [CTD_profiles_processing.ipynb](https://github.com/IrishMarineInstitute/mi-ctd-data-processing/blob/main/CTD_Profiles_Processing.ipynb)
2. Calibrations
3. Quality Checks

## Setup on Windows 

### 1. Download the Jupyter Notebook from [Github](https://github.com/nvdsteen/mi-ctd-data-processing/archive/refs/heads/main.zip)
> [!NOTE]  
> install in the directory of your choice; This is where you’ll start the notebook from.

### 2. Download SBEDataProcessing software and manual
   - Manual:  https://epic.awi.de/id/eprint/38965/1/SBEDataProcessing_7_23_2.pdf
   - Software: https://www.seabird.com/asset-get.download.jsa?code=251838 

### 3. Download **Python 3.12** https://www.python.org/downloads/windows/                                                                                                                 
   - install Python, **note the path**!
   - add path to environmental variable. Go to search bar, find environmental variable, click on `Path`, add a new variable with the path to the recently installed Python software.
   - Open the command line window and check python version: `python --version`

> [!NOTE]
> If python is not found: Disable Application aliases. Go to search bar, find App execution aliases, find the Python aliases and disable them.

                                                                    
### 4. Installation Notebook
  - Go to the notebook folder and activate the virtual environment: `Scripts\activate`
  - Install requirements: `pip install -Ur mi-ctd-data-processing\requirements.txt`
  - Install notebook: `pip install notebook`
  - Start Jupyter notebook: go to mi-ctd-data-processing and type: `jupyter notebook`
> [!NOTE]
> A new page will open in your web browser.

          
### 5. Creation of a batch file to start the notebook (including the virtual environment activation)
  - open Notepad, type:
  ```bat
  call path\to\activate\file
  cd path\to\notebook
  jupyter notebook
  ```
  - Save as `xxx.bat`

> [!NOTE]
> To launch the notebook, just double click on the bat file.
    

## CTD Data Processing Jupyter Notebook
The purpose of this notebook was to create a consistent set of data processing steps that could be used both at sea, with limited internet access, and back in the office/laboratory. Following on from this it was decided to make the notebook more accessible and usable to scientists other than physical oceanographers (eg. chemists and fisheries scientists). This allows them to provisionally process CTD data on their research cruises and generate indicative plots of the water masses they are moving through while at sea. The notebook has automated CTD Data Processing, reducing processing time and workload on physical oceanographers. 

A data processing routine was designed based on a scientific consensus with contributions from international scientific groups to address the main challenges we faced within our organisation with processing CTD data. The routine uses Sea-Bird Data Processing software through a Jupyter Notebook written in Python. The use of Sea-Bird software requires running the notebook on a Windows machine. To find out more about Sea-Bird software and how to download it click [here](https://software.seabird.com/)

The notebook was developed using Python 3.12 and requires the following python packages and versions. A set of commands to install these through Anaconda can be found [here](https://github.com/IrishMarineInstitute/mi-ctd-data-processing/blob/main/anaconda_env_setup_commands.txt)
* chevron=0.14.0
* numpy=1.26.4
* pandas=2.2.2
* pyodbc=5.0.1
* seawater=3.3.5
* bokeh=3.5.1
* xlrd=2.0.1
* widgetsnbextension=3.6.1
* jupyterlab_widgets

A set of supporting scripts can be found in the [scripts](https://github.com/IrishMarineInstitute/mi-ctd-data-processing/tree/main/scripts) folder and PSA templates needed to files to configure the SBE processing steps can be found in the [psa_templates](https://github.com/IrishMarineInstitute/mi-ctd-data-processing/tree/main/psa_templates) folder.

## Quality Checks Jupyter Notebook
*To be completed*
## Calibrations Notebook
*To be completed*

**To cite this work please reference:**

*INSERT CITATION WHEN AVAILABLE*
