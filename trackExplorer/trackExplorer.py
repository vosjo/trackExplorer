 
#Load the packages
import os
import io
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file

import urllib

from bokeh.models import ColumnDataSource, Select
from bokeh.embed import components
from bokeh.layouts import layout, gridplot, Spacer
from bokeh.models.widgets import Panel, Tabs, Div

# added try catch to allow local running of the code without heroku
try:
    from trackExplorer import plotting, drive_access
    from trackExplorer.fileio import read_history
except:
    import plotting, drive_access
    from fileio import read_history

DOWNLOAD_FOLDER = os.path.join('trackExplorer','downloads')

if not os.path.isdir(DOWNLOAD_FOLDER):
    os.mkdir(DOWNLOAD_FOLDER)

#Connect the app
app = Flask(__name__, static_url_path='/static')
app.secret_key = os.urandom(24)
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER

#Get the grid list
grid_list = drive_access.grid_list

start_pars = {'x1': 'M1_init',
              'y1': 'q_init',
              'z1': 'product',
              'x2': 'M1_init',
              'y2': 'P_init',
              'z2': 'product',
            }

history_pars = {'x': 'model_number',
                'y1': 'period_days',
                'y2': 'log_LHe',
                'y3': 'lg_mstar_dot_1',
                'y4': 'rl_overflow_1',
                'y5': 'R1_div_a',
                'y6': 'log10_J_div_Jdot_div_P',}


def read_summary(gridname, start_pars):

    summary_df = drive_access.get_summary_file(gridname)
    columns = summary_df.columns.values.tolist()

    for par in start_pars.keys():
        summary_df[par] = summary_df[start_pars[par]]

    return summary_df, columns


def read_evolution_model(grid_name, filename, history_pars, folder_name=None, model_folder_name=None):

    evolution_df = drive_access.get_track(grid_name, filename,
                                          folder_name=folder_name, model_folder_name=model_folder_name)

    if evolution_df is None:
        keys = ['log_Teff', 'log_Teff_2', 'log_g', 'log_g_2', 'log_center_Rho', 'log_center_Rho_2',
                'log_center_T', 'log_center_T_2'] + list(history_pars.keys())
        result = {val: [] for val in keys}
        return pd.DataFrame(data=result), keys

    for par in history_pars.keys():
        if history_pars[par] in evolution_df:
            evolution_df[par] = evolution_df[history_pars[par]]
        else:
            evolution_df[par] = evolution_df.loc[0]

    evolution_columns = evolution_df.columns.values.tolist()

    return evolution_df, evolution_columns


def get_track_from_grid(grid, grid_name, history_pars):

    folder_name, model_folder_name = None, None

    grid_columns = grid.index.values.tolist()

    if 'folder_name' in grid_columns and 'model_folder_name' in grid_columns:
        folder_name = grid['folder_name']
        model_folder_name = grid['model_folder_name']

    filename = grid['path'].split('/')[-1]

    track_df, track_columns = read_evolution_model(grid_name, filename, history_pars,
                                                           folder_name=folder_name, model_folder_name=model_folder_name)

    return track_df, track_columns


@app.route('/history', methods=['POST'])
def history_data():
    # returns JSON data when requested. Used to update datasource with ajax

    data = request.get_json(force=True)
    gridname = data.get('grid_name')
    filename = data.get('file_name')
    filename = filename.split('/')[-1]
    folder_name = data.get('folder_name', None)
    model_folder_name = data.get('model_folder_name', None)
    updated_pars = data.get('history_pars')

    print(gridname, filename, folder_name, model_folder_name, updated_pars)

    new_pars = history_pars.copy()
    new_pars.update(updated_pars)
    evolution_df, evolution_columns = read_evolution_model(gridname, filename, history_pars=new_pars,
                                                           folder_name=folder_name, model_folder_name=model_folder_name)

    data_dict = {}
    for col in evolution_columns:
        data_dict[col] = evolution_df[col].values.tolist()
    data_dict['index'] = list(range(len(data_dict[col])))

    return jsonify(data_dict)


@app.route('/download_history', methods=['POST'])
def download_history_data():
    """
    This view will return the url from which the track.h5 file can be downloaded.
    The frontend is responsible for sending a post request to download_and_remove with the filename to actually get
    the file.
    """

    data = request.get_json(force=True)
    gridname = data.get('grid_name')
    filename = data.get('file_name')
    filename = filename.split('/')[-1]
    folder_name = data.get('folder_name', None)
    model_folder_name = data.get('model_folder_name', None)

    track_filename = app.config['DOWNLOAD_FOLDER'] + '/' + filename

    track_filename = drive_access.get_track(gridname, filename, folder_name=folder_name,
                           model_folder_name=model_folder_name, save_filename=track_filename)

    print('download_history_data: ', track_filename)

    return jsonify({'url': '/download_history/'+track_filename})


@app.route('/download_history/<filename>')
def download_and_remove(filename):

    path = os.path.join(app.config['DOWNLOAD_FOLDER'], filename)

    def generate():
        with open(path, 'rb') as f:
            yield from f

        os.remove(path)

    r = app.response_class(generate(), mimetype='application/octet-stream')
    r.headers.set('Content-Disposition', 'attachment', filename=filename)
    return r


@app.route('/')
def homepage():
    grid_name = request.args.get('grid', grid_list['name'][0])

    summary_df, summary_columns = read_summary(grid_name, start_pars)
    evolution_df, evolution_columns = get_track_from_grid(summary_df.iloc[0], grid_name, history_pars)

    # get the data sources
    source = ColumnDataSource(data=summary_df)
    evolution_source = ColumnDataSource(data=evolution_df)
    parameters = summary_df.columns.values.tolist()
    for p in ['x1', 'y1', 'z1', 'x2', 'y2', 'z2']:
        parameters.remove(p)
    values = [0 for i in parameters]
    table_source = ColumnDataSource(data={'parameters': parameters, 'values': values})
      
    # Setup plot
    plot, p1, p2 = plotting.make_summary_plot(source, table_source, start_pars)
    cm_plot, cm_p1, cm_p2 = plotting.make_Gaia_CM_diagram(source, table_source)
    controls, button, dl_button, control_dict = plotting.make_summary_controls(source, evolution_source, p1, p2, start_pars, summary_columns)
    table = plotting.make_summary_table(table_source)

    hr_plot = plotting.make_HR_diagram(evolution_source)
    center_plot = plotting.make_center_track(evolution_source)

    history_plots, figures = plotting.make_history_plots([evolution_source], history_pars)
    history_controls = plotting.make_history_controls([evolution_source], history_pars, evolution_columns, figures)
    
    # create layout
    summary_controls = layout([[plot], [controls]])
    table_header = Div(text="<h2>Selected Model</h2>", height=40, sizing_mode="stretch_width")
    table_button = layout([[table_header], [table], [Spacer(width=10, height=20)], [button], [dl_button]])

    tab1 = Panel(child=summary_controls, title="Grid summary")
    tab2 = Panel(child=cm_plot, title="Gaia Color-Magnitude")
    tab_plot = Tabs(tabs=[tab1, tab2])

    summary_layout = layout([[tab_plot, Spacer(width=40, height=10), table_button]])

    properties_plot = gridplot([[hr_plot, center_plot]], toolbar_location='right')
    
    history_plot = layout([[history_controls], [history_plots]])
    
    script, div = components((summary_layout, properties_plot, history_plot))

    # Render the page
    return render_template('home.html',
                           script=script, summary_div=div[0], properties_div=div[1], history_div=div[2],
                           grids=grid_list['name'], selected_grid=grid_name)


@app.route('/compare_models')
def compare_models():
    grid1 = request.args.get('grid1', grid_list['name'][0])
    grid2 = request.args.get('grid2', grid_list['name'][1])
    join = request.args.get('join', 'path')

    grid1_df, columns1 = read_summary(grid1, {})
    grid2_df, columns2 = read_summary(grid2, {})

    # select only columns available in both grids
    grid_columns = [value for value in columns1 if value in columns2]
    grid1_df = grid1_df[grid_columns]
    grid2_df = grid2_df[grid_columns]

    # merge the data frames
    grid_df = pd.merge(grid1_df, grid2_df, how='inner', on=join, suffixes=('_1', '_2'))

    # add the x1, y1, x2 and y2 default columns necessary for the plot to work
    start_pars = {'x1': 'M1_init_1',
                  'y1': 'q_init_1',
                  'x2': 'M1_init_2',
                  'y2': 'q_init_2', }
    for par in start_pars.keys():
        grid_df[par] = grid_df[start_pars[par]]

    grid_source = ColumnDataSource(data=grid_df)

    # obtain the individual tracks
    track1_df, track_columns = get_track_from_grid(grid1_df.iloc[0], grid1, history_pars)
    track1_source = ColumnDataSource(data=track1_df)
    track2_df, track_columns = get_track_from_grid(grid2_df.iloc[0], grid2, history_pars)
    track2_source = ColumnDataSource(data=track2_df)

    disp_pars = {'x1': 'M1_init',
                 'y1': 'q_init',
                 'x2': 'M1_init',
                 'y2': 'q_init', }

    # grid comparison plots
    plot, p1, p2 = plotting.make_comparison_plot(grid_source, disp_pars, titles=[grid1, grid2])
    controls, control_dict = plotting.make_comparison_controls(grid_source, [track1_source, track2_source], p1, p2,
                                                               disp_pars, grid_columns)
    comparison_layout = layout([[plot], [controls]])

    # track plots
    history_plots, figures = plotting.make_history_plots([track1_source, track2_source], history_pars)
    history_controls = plotting.make_history_controls([track1_source, track2_source], history_pars, track_columns,
                                                      figures)
    history_layout = layout([[history_controls], [history_plots]])

    script, div = components((comparison_layout, history_layout))

    return render_template('compare_models.html',
                           grid1=grid1, grid2=grid2, grids=grid_list['name'], join=join, columns=grid_columns,
                           script=script, comparison_plot=div[0], history_plot=div[1])

if __name__ == '__main__':
    app.run(debug=True, threaded=True) # Set to false when deploying
