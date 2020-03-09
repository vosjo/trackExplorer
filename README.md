# Track Explorer

Track explorer is a small web app that can be used to easily analyse a grid of MESA models. It is written in python
using Flask using Bokeh for the interactive plots. Data is pulled from a google drive shared between the collaborators
on the project using the google drive API.

An online instance is running on Heroku here: https://sheltered-wave-29753.herokuapp.com/ (this is a free dyno and
can be rather slow)

![trackexplorer_screenshot](docs/trackexplorer_app.png)

## Installation on Heroku

Follow the standard instructions to deploy a python app on Heroku: 
https://devcenter.heroku.com/articles/getting-started-with-python

Use a google service account for the app access to google drive. See 
https://cloud.google.com/iam/docs/creating-managing-service-accounts to create a service account. Make sure to give
the service account access to your google drive

Do not store the credentials of the service account in your code base. Use heroku config vars to store the credentials.
I use this build pack to deal with the credentials: https://github.com/elishaterada/heroku-google-application-credentials-buildpack 