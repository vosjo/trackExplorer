# Track Explorer

Track explorer is a small web app that can be used to easily analyse a grid of MESA models. It is written in python
using Flask and Bokeh for the interactive plots. Data is pulled from a google drive shared between the collaborators
on the project using the google drive API.

An online instance is running on Heroku here: https://sheltered-wave-29753.herokuapp.com/ (this is a free dyno and
can be rather slow, although the main bottleneck remains fetching data from a google drive)

Track explorer was specifically designed to deal with the output of [NNaPS](https://github.com/vosjo/nnaps)

![trackexplorer_screenshot](docs/trackexplorer_app.png)

## Setup

Track Explorer loads all data from a google drive. You will have to setup a google service account for the app access 
google drive. This is explained well here: https://cloud.google.com/iam/docs/creating-managing-service-accounts
Make sure to give the service account access to the drive where you are storing all models.

The standard file structure that Track explorer expects is the following:

::

    Google Drive
    ├── trackExplorer
    |   └── Model_grid_info
    ├── Grid name
    │   ├── hdf5 compressed tracks
    |   │   ├── track1.h5
    |   │   ├── track2.h5
    |   |   └── trackn.h5
    |   └── extracted_parameter_file.csv
    ├── BPS_L3_grid
    │   ├── processed_L3_h5
    |   │   ├── M1.00_0.95_P320_FeH-0.25.h5
    |   │   ├── M1.24_0.73_P128_FeH-0.84.h5
    |   |   └── M2.53_1.71_P572_FeH+0.12.h5
    │   ├── BPS_L3_alpha_0.6.csv
    |   └── BPS_L3_alpha_0.3.csv

Track explorer will look for a google sheet that contains a list of all model runs that you want it to display. It 
expects this file in a folder called 'trackExplorer', and the sheet itself shoud be named 'Model_grid_info'
The expected structure of this file is the following:

|   name  | folder_name | summary_file         | model_folder_name | info            |
|---------|-------------|----------------------|-------------------|-----------------|
| L3 grid | BPS_L3_grid	| BPS_L3_alpha_0.3.csv | processed_L3_h5   | CE: alpha=0.3   |
| L3 grid | BPS_L3_grid	| BPS_L3_alpha_0.6.csv | processed_L3_h5   | CE: alpha=0.6   |

- **name** is the name that Track explorer will use to call the model grid
- **folder_name** is the name of the folder in the google drive containing the summary file and the folder 
containing the processed tracks
- **summary_file** is the name of the csv file containing all extracted parameters that you want Track explorer to 
display, 
- **model_folder_name** is the folder inside the main grid folder containing the compressed models in hdf5 format.
- **info** is a column to store extra info on a grid. it is not currently displayed by track explorer.

When deployed on Heroku, Track explorer will automatically fetch the Model_grid_info when a Heroku slug is spun up. Due
to how Heroku operates, a free node will not maintain its state so the Model_grid_info will be frequently refreshed. If
you deploy on another platform, you might need to adjust in the code to update the file on a regular basis, e.g. with a 
cron script. 

## Model data to display

Track explorer was specifically designed to deal with the output of [NNaPS](https://github.com/vosjo/nnaps), but can
display any type of model output as long as it is in csv format. The tracks however have to be in a specific format used
by NNaPS to be interpreted by Track explorer. 

A typical use case would be: You have a grid of MESA models calculated and what to investigate the results. You use 
nnaps-mesa to first compress all MESA runs to hdf5 format that you store on a google drive shared with your 
collaborators. Then you use nnaps-mesa to extract all parameters of interest from those runs and save them as a csv file 
that you also upload to that same google drive. Now you and your collaborators can use Track explorer to explore both 
the extracted parameters and the tracks of the MESA models from which they were extracted, all from your web browser
without the need to share code.


## Installation on Heroku

Follow the standard instructions to deploy a python app on Heroku: 
https://devcenter.heroku.com/articles/getting-started-with-python

Do not store the credentials of the google service account in your code base. Use heroku config vars to store the 
credentials. I use this build pack to deal with the credentials: 
https://github.com/elishaterada/heroku-google-application-credentials-buildpack 