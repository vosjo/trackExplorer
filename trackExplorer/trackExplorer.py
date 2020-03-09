 
#Load the packages
import pandas as pd
from flask import Flask, render_template, request, jsonify

import urllib

from bokeh.models import ColumnDataSource, Select
from bokeh.embed import components
from bokeh.layouts import layout, gridplot

# added try catch to allow local running of the code without heroku
try:
    from trackExplorer import plotting, drive_access
    from trackExplorer.fileio import read_history
except:
    import plotting, drive_access
    from fileio import read_history

#Connect the app
app = Flask(__name__)

#Get the grid list
grid_list = drive_access.grid_list

summary_df, evolution_df = None, None
columns, evolution_columns = [], []

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


def read_summary(gridname, start_pars):
    global summary_df, columns

    summary_df = drive_access.get_summary_file(gridname)
    columns = summary_df.columns.values.tolist()

    for par in start_pars.keys():
        summary_df[par] = summary_df[start_pars[par]]


def read_evolution_model(gridname, filename, history_pars):
    global evolution_columns, evolution_df

    evolution_df = drive_access.get_track(gridname, filename)

    for par in history_pars.keys():
        evolution_df[par] = evolution_df[history_pars[par]]

    evolution_columns = evolution_df.columns.values.tolist()


read_summary(grid_list['name'][0], start_pars)
filename = summary_df['filename'][0].split('/')[-1]
read_evolution_model(grid_list['name'][0], filename, history_pars=history_pars)


@app.route('/history', methods=['POST'])
def history_data():
    # returns JSON data when requested. Used to update datasource with ajax

    data = request.get_json(force=True)
    filename = data.get('filename')
    filename = filename.split('/')[-1]
    updated_pars = data.get('history_pars')

    new_pars = history_pars.copy()
    new_pars.update(updated_pars)
    read_evolution_model(grid_list['name'][0], filename, history_pars=new_pars)

    data_dict = {}
    for col in evolution_df.columns.values.tolist():
        data_dict[col] = evolution_df[col].values.tolist()

    return jsonify(data_dict)



@app.route('/')
def homepage():
   
    # get the data sources
    source = ColumnDataSource(data=summary_df)
    evolution_source = ColumnDataSource(data=evolution_df)
    
    # make the grid selector
    grids_selector = Select(title='Available Grids:', value=grid_list['name'].values.tolist()[0], options=grid_list['name'].values.tolist())
      
    # Setup plot
    plot, p1, p2 = plotting.make_summary_plot(source, start_pars)
    controls, control_dict = plotting.make_summary_controls(source, evolution_source, p1, p2, start_pars, columns)

    hr_plot = plotting.make_HR_diagram(evolution_source)
    center_plot = plotting.make_center_track(evolution_source)

    history_plots, figures = plotting.make_history_plots(evolution_source, history_pars)
    history_controls = plotting.make_history_controls(evolution_source, history_pars, evolution_columns, figures)
    
    # create layout
    summary_plot = layout([[plot, controls]])

    properties_plot = gridplot([[hr_plot, center_plot]], toolbar_location='right')
    
    history_plot = layout([[history_controls], [history_plots]])
    
    script, div = components((grids_selector, summary_plot, properties_plot, history_plot))

    # Render the page
    return render_template('home.html', script=script, grid_selection=div[0], summary_div=div[1], properties_div=div[2], history_div=div[3])


if __name__ == '__main__':
    app.run(debug=True) # Set to false when deploying
