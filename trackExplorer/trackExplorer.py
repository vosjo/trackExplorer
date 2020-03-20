 
#Load the packages
import pandas as pd
from flask import Flask, render_template, request, jsonify

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

#Connect the app
app = Flask(__name__)

#Get the grid list
grid_list = drive_access.grid_list

start_pars = {'x1': 'M1_init',
              'y1': 'q_init',
              'x2': 'M1_init',
              'y2': 'P_init',
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


def read_evolution_model(gridname, filename, history_pars, folder_name=None, model_folder_name=None):

    evolution_df = drive_access.get_track(gridname, filename,
                                          folder_name=folder_name, model_folder_name=model_folder_name)

    if evolution_df is None:
        keys = ['log_Teff', 'log_Teff_2', 'log_g', 'log_g_2', 'log_center_Rho', 'log_center_Rho_2',
                'log_center_T', 'log_center_T_2'] + list(history_pars.keys())
        result = {val: [] for val in keys}
        return pd.DataFrame(data=result), keys

    for par in history_pars.keys():
        evolution_df[par] = evolution_df[history_pars[par]]

    evolution_columns = evolution_df.columns.values.tolist()

    return evolution_df, evolution_columns


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

    new_pars = history_pars.copy()
    new_pars.update(updated_pars)
    evolution_df, evolution_columns = read_evolution_model(gridname, filename, history_pars=new_pars,
                                                           folder_name=folder_name, model_folder_name=model_folder_name)

    data_dict = {}
    for col in evolution_columns:
        data_dict[col] = evolution_df[col].values.tolist()
    data_dict['index'] = list(range(len(data_dict[col])))

    return jsonify(data_dict)



@app.route('/')
def homepage():
    gridname = request.args.get('grid', grid_list['name'][0])

    summary_df, summary_columns = read_summary(gridname, start_pars)
    folder_name, model_folder_name = None, None
    if 'folder_name' in summary_columns and 'model_folder_name' in summary_columns:
        folder_name = summary_df['folder_name'][0]
        model_folder_name = summary_df['model_folder_name'][0]
    evolution_df, evolution_columns = read_evolution_model(gridname, summary_df['path'][0].split('/')[-1], history_pars,
                                                           folder_name=folder_name, model_folder_name=model_folder_name)

    # get the data sources
    source = ColumnDataSource(data=summary_df)
    evolution_source = ColumnDataSource(data=evolution_df)
    parameters = summary_df.columns.values.tolist()
    for p in ['x1', 'y1', 'x2', 'y2']:
        parameters.remove(p)
    values = [0 for i in parameters]
    table_source = ColumnDataSource(data={'parameters': parameters, 'values': values})
    
    # make the grid selector
    grids_selector = Select(title='Available Grids:', value=grid_list['name'].values.tolist()[0], options=grid_list['name'].values.tolist())
      
    # Setup plot
    plot, p1, p2 = plotting.make_summary_plot(source, table_source, start_pars)
    cm_plot, cm_p1, cm_p2 = plotting.make_Gaia_CM_diagram(source, table_source)
    controls, button, control_dict = plotting.make_summary_controls(source, evolution_source, p1, p2, start_pars, summary_columns)
    table = plotting.make_summary_table(table_source)

    hr_plot = plotting.make_HR_diagram(evolution_source)
    center_plot = plotting.make_center_track(evolution_source)

    history_plots, figures = plotting.make_history_plots(evolution_source, history_pars)
    history_controls = plotting.make_history_controls(evolution_source, history_pars, evolution_columns, figures)
    
    # create layout
    # layout1 = layout([[plot, Spacer(width=40, height=10), table]])
    summary_controls = layout([[plot], [controls]])
    table_header = Div(text="<h2>Selected Model</h2>", height=40, sizing_mode="stretch_width")
    table_button = layout([[table_header], [table], [Spacer(width=10, height=20)], [button]])

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
                           grids=grid_list['name'], selected_grid=gridname)


@app.route('/compare_models')
def compare_models():
    grid1 = request.args.get('grid1', grid_list['name'][0])
    grid2 = request.args.get('grid2', grid_list['name'][1])
    join = request.args.get('join', 'path')

    grid1_df, columns1 = read_summary(grid1, {})
    grid2_df, columns2 = read_summary(grid2, {})

    # select only columns available in both grids
    columns = [value for value in columns1 if value in columns2]
    grid1_df = grid1_df[columns]
    grid2_df = grid2_df[columns]

    # merge the dataframes
    grid_df = pd.merge(grid1_df, grid2_df, how='inner', on=join, suffixes=('_1', '_2'))

    # add the x1, y1, x2 and y2 default columns necessary for the plot to work
    start_pars = {'x1': 'M1_init_1',
                  'y1': 'q_init_1',
                  'x2': 'M1_init_2',
                  'y2': 'q_init_2',}
    for par in start_pars.keys():
        grid_df[par] = grid_df[start_pars[par]]

    source = ColumnDataSource(data=grid_df)

    disp_pars = {'x1': 'M1_init',
                 'y1': 'q_init',
                 'x2': 'M1_init',
                 'y2': 'q_init', }

    plot, p1, p2 = plotting.make_comparison_plot(source, disp_pars, titles=[grid1, grid2])
    controls, control_dict = plotting.make_comparison_controls(source, p1, p2, disp_pars, columns)

    comparison_plot = layout([[plot], [controls]])

    script, div = components(comparison_plot)

    return render_template('compare_models.html',
                           grid1=grid1, grid2=grid2, grids=grid_list['name'], join=join, columns=columns,
                           script=script, comparison_plot=div)


if __name__ == '__main__':
    app.run(debug=True) # Set to false when deploying
