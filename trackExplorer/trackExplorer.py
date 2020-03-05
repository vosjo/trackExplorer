 
#Load the packages
import pandas as pd
from flask import Flask, render_template, request, jsonify

import urllib

from bokeh.models import ColumnDataSource
from bokeh.embed import components
from bokeh.layouts import layout, gridplot

# added try catch to allow local running of the code without heroku
try:
    from trackExplorer import plotting
    from trackExplorer.fileio import read_history
except:
    import plotting
    from fileio import read_history

#Connect the app
app = Flask(__name__)

#Get the data, from somewhere
summary_df = pd.read_csv('http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/BPS_shortP_Potsdam_4_J_div_Jdot_div_P_10.csv')
columns = summary_df.columns.values.tolist()

start_pars = {'x1': 'M1',
              'y1': 'qinit',
              'color1': 'FeHinit',
              'x2': 'M1',
              'y2': 'Pinit',
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


def read_evolution_model(url, history_pars):

    global evolution_columns, evolution_df

    filename, _ = urllib.request.urlretrieve(url)

    data = read_history(filename)
    data = pd.DataFrame(data)

    for par in history_pars.keys():
        data[par] = data[history_pars[par]]

    evolution_df = data
    evolution_columns = data.columns.values.tolist()

read_evolution_model('http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/BPS_shortP_Potsdam_4_hdf5/M2.643_M1.013_P28.40_Z0.00420.hdf5',
                     history_pars=history_pars)


@app.route('/history', methods=['POST'])
def history_data():
    # returns JSON data when requested. Used to update datasource with ajax

    data = request.get_json(force=True)
    filename = data.get('filename')
    updated_pars = data.get('history_pars')

    url = 'http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/'+filename

    new_pars = history_pars.copy()
    new_pars.update(updated_pars)
    read_evolution_model(url, history_pars=new_pars)

    data_dict = {}
    for col in evolution_df.columns.values.tolist():
        data_dict[col] = evolution_df[col].values.tolist()

    return jsonify(data_dict)



@app.route('/')
def homepage():
   
    # get the data sources
    source = ColumnDataSource(data=summary_df)
    evolution_source = ColumnDataSource(data=evolution_df)
      
    # Setup plot
    plot, p1, p2 = plotting.make_summary_plot(source, start_pars)
    controls, control_dict = plotting.make_summary_controls(source, evolution_source, p1, p2, start_pars, columns)

    hr_plot = plotting.make_HR_diagram(evolution_source)
    center_plot = plotting.make_center_track(evolution_source)

    history_plots, figures = plotting.make_history_plots(evolution_source, history_pars)
    history_controls = plotting.make_history_controls(evolution_source, history_pars, evolution_columns, figures)
    
    # create layout
    summary_plot = layout([[plot, controls]])

    properties_plot = gridplot([[hr_plot, center_plot]])
    
    history_plot = layout([[history_controls], [history_plots]])
    
    script, div = components((summary_plot, properties_plot, history_plot))

    # Render the page
    return render_template('home.html', script=script, summary_div=div[0], properties_div=div[1], history_div=div[2])


if __name__ == '__main__':
    app.run(debug=True) # Set to false when deploying
