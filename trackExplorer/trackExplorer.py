 
#Load the packages
import pandas as pd
from flask import Flask, render_template, request

import urllib

from bokeh.models import ColumnDataSource
from bokeh.embed import components
from bokeh.layouts import layout

from trackExplorer.plotting import make_summary_plot, make_summary_controls, make_history_plots, make_history_controls
from trackExplorer.fileio import read_history

#Connect the app
app = Flask(__name__)

#Get the data, from somewhere
summary_df = pd.read_csv('http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/BesanconLargeNew1.csv')
columns = summary_df.columns.values.tolist()

start_pars = {'x1': 'M1',
              'y1': 'qinit',
              'color1': 'FeHinit',
              'x2': 'Zinit', 
              'y2': 'Pinit_frac',
              'color2': 'M1',
            }

history_pars = {'x': 'model_number',
                'y1': 'period_days',
                'y2': 'log_LHe',
                'y3': 'lg_mstar_dot_1',
                'y4': 'rl_overflow_1',
                'y5': 'R1_div_a',
                'y6': 'log10_J_div_Jdot_div_P',}

for  par in start_pars.keys():
    summary_df[par] = summary_df[start_pars[par]]


evolution_df = None
evolution_columns = []

def read_evolution_model(url):

    global evolution_columns, evolution_df

    filename, _ = urllib.request.urlretrieve(url)

    data = read_history(filename)
    data = pd.DataFrame(data)

    for par in history_pars.keys():
        data[par] = data[history_pars[par]]

    evolution_df = data
    evolution_columns = data.columns.values.tolist()

read_evolution_model('http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/BesanconLarge_hdf5/M0.851_M0.842_P234.84_Z0.0005.hdf5')



@app.route('/')
def homepage():
   
    # get the data sources
    source = ColumnDataSource(data=summary_df)
    evolution_source = ColumnDataSource(data=evolution_df)
      
    #Setup plot    
    plot, p1, p2 = make_summary_plot(source, start_pars)
    controls, control_dict = make_summary_controls(source, p1, p2, start_pars, columns)
    
    history_plots = make_history_plots(evolution_source, history_pars)
    history_controls = make_history_controls(evolution_source, history_pars, evolution_columns)
    
    #create layout
    summary_plot = layout([[plot, controls]])
    
    history_plot = layout([[history_controls], [history_plots]])
    
    script, div = components((summary_plot, history_plot))

    #Render the page
    return render_template('home.html', script=script, summary_div=div[0], history_div=div[1])    


if __name__ == '__main__':
    app.run(debug=True) #Set to false when deploying
