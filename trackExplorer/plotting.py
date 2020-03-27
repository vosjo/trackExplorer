import itertools

from bokeh import models as mpl
from bokeh.models import CustomJS, Select, Button, CheckboxGroup, TableColumn, StringFormatter, DataTable, CDSView, BooleanFilter
from bokeh.transform import linear_cmap, factor_cmap, factor_mark, transform
from bokeh.plotting import figure
from bokeh.layouts import gridplot, row, column, layout, widgetbox, Spacer
from bokeh.palettes import Category10

from pathlib import Path
import pandas as pd

base_path = Path(__file__).parent

# boundaries
edegeneracy = pd.read_csv(base_path / 'plot_info/kap_rad_cond_eq.data', sep='\s+', names=['rho', 'T'])
HIgnition = pd.read_csv(base_path / 'plot_info/hydrogen_burn.data', sep='\s+', names=['rho', 'T'])
HeIgnition = pd.read_csv(base_path / 'plot_info/helium_burn.data', sep='\s+', names=['rho', 'T'])
OIgnition = pd.read_csv(base_path / 'plot_info/carbon_burn.data', sep='\s+', names=['rho', 'T'])

# Gaia hiparcos sample
hiparcos = pd.read_csv(base_path / 'plot_info/1Kpc_Hiparchos_sample_cut.csv', sep='\s+')


def make_summary_plot(source, table_source, pars_dict):
    
    tools = "pan,wheel_zoom,box_zoom,box_select,tap,hover,reset,crosshair"

    pars = ['M1_init', 'M2_init', 'P_init', 'q_init', 'product', 'stability', 'termination_code']
    basic_tooltip = [(p, '@'+p) for p in pars]

    PRODUCTS = ['HB', 'He-WD', 'CE', 'UK', 'failed', 'sdB', 'sdA'] + \
               ['stable', 'CE', 'contact', 'merger']
    MARKERS = ['square', 'triangle', 'asterisk', 'asterisk', 'diamond', 'circle', 'circle'] + \
              ['circle', 'diamond', 'square', 'triangle', ]
    COLORS = ['red', 'green', 'purple', 'purple', 'gray', 'blue', 'orange'] + \
             ['red', 'green', 'blue', 'gray']
    SIZES = [7, 7, 7, 7, 15, 7]

    v_func = """
            const norm = new Float64Array(xs.length)
            for (let i = 0; i < xs.length; i++) {
                if (xs[i] == 'sdB' || xs[i] == 'Fail' || xs[i] == 'CE') {
                        norm[i] = 15
                } else {
                        norm[i] = 7
                }
            }
            return norm
            """
    size_transform = mpl.CustomJSTransform(v_func=v_func)
    
    # Left Figure
    p1 = figure(x_axis_label=pars_dict['x1'], y_axis_label=pars_dict['y1'], active_drag='box_select',
                tools=tools, tooltips=basic_tooltip)
    
    p1.scatter(x="x1", y="y1", source=source, fill_alpha=0.4,
            size=transform('z1', size_transform),
            color=factor_cmap('z1', COLORS, PRODUCTS),
            marker=factor_mark('z1', MARKERS, PRODUCTS),)  # legend_group="z1",

    # Right Figure
    p2 = figure(x_axis_label=pars_dict['x2'], y_axis_label=pars_dict['y2'], active_drag='box_select',
                tools=tools, tooltips=basic_tooltip)
    
    p2.scatter(x="x2", y="y2", source=source, fill_alpha=0.4,
            size=transform('z2', size_transform),
            color=factor_cmap('z2', COLORS, PRODUCTS),
            marker=factor_mark('z2', MARKERS, PRODUCTS),)  # legend_group="z2",
    
    # color_bar2 = mpl.ColorBar(color_mapper=color_mapper, location=(0,0), title=pars_dict['color2'], title_text_font_size='12pt')
    # p2.add_layout(color_bar2, 'right')

    plot = gridplot([[p1,p2]])
    
    # add interaction when selecting a model
    callback = CustomJS(args=dict(summary_source=source, table_source=table_source), code="""
            selected_indices = summary_source.selected.indices;
            
            console.log(summary_source.selected.indices[0]);
            console.log(summary_source);
            
            if (summary_source.selected.indices.length > 0){
                var data = summary_source.data;
                var ind = summary_source.selected.indices[0];
                var parameters = table_source.data['parameters']
                var values = table_source.data['values']
                
                parameters.forEach(function (par, index) {
                    values[index] = data[par][ind];
                });
                
                //table_source.data['parameters'] = x;
                table_source.data['values'] = values;
                
                table_source.change.emit();
            }
            
            """)
    p1.js_on_event('tap', callback)
    p2.js_on_event('tap', callback)
    
    return plot, p1, p2


def make_summary_controls(source, history_source, p1, p2, pars_dict, select_options):

    calbackcode = """
        var data = source.data;
        var parname = cb_obj.value;
        data[axisname] = data[parname];
        summary_pars[axisname] = parname; //store the parameter name in a global variable
        if (axis != '') {
            axis.axis_label = parname;
        }
        source.change.emit();
    """

    x1 = Select(title='X-Axis 1', value=pars_dict['x1'], options=select_options)
    x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x1', axis=p1.xaxis[0]), code=calbackcode))

    y1 = Select(title='Y-Axis 1', value=pars_dict['y1'], options=select_options)
    y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='y1', axis=p1.yaxis[0]), code=calbackcode))

    z1 = Select(title='Marker', value=pars_dict['z1'], options=['product', 'stability'])
    z1.js_on_change('value', CustomJS(args=dict(source=source, axisname='z1', axis=''), code=calbackcode))

    x2 = Select(title='X-Axis 2', value=pars_dict['x2'], options=select_options)
    x2.js_on_change('value', CustomJS(args=dict(source=source, axisname='x2', axis=p2.xaxis[0]), code=calbackcode))

    y2 = Select(title='Y-Axis 2', value=pars_dict['y2'], options=select_options)
    y2.js_on_change('value', CustomJS(args=dict(source=source, axisname='y2', axis=p2.yaxis[0]), code=calbackcode))

    z2 = Select(title='Marker', value=pars_dict['z2'], options=['product', 'stability'])
    z2.js_on_change('value', CustomJS(args=dict(source=source, axisname='z2', axis=''), code=calbackcode))

    update_source = CustomJS(args=dict(summary_source=source, history_source=history_source), code="""
        update_source(summary_source, history_source, grid_name, '')
        """)
    
    button = Button(label="Plot selected track", button_type="success", sizing_mode="stretch_width")
    button.js_on_click(update_source)


    # create sumary plots
    # controls1 = widgetbox(x1, y1, width=300)
    # controls2 = widgetbox(x2, y2, width=300)
    # controls = column([controls1, controls2, button])

    controls = column([row([x1, y1, x2, y2]), row([z1, z2])])

    control_dict = {"x1": x1,
                    "y1": y1,
                    "z1": z1,
                    "x2": x2,
                    "y2": y2,
                    "z2": z2,
                    }

    return controls, button, control_dict


def make_Gaia_CM_diagram(source, table_source):
    tools = "pan,wheel_zoom,box_zoom,box_select,tap,hover,reset,crosshair"

    pars = ['M1_init', 'M2_init', 'P_init', 'q_init', 'product', 'stability', 'termination_code']
    basic_tooltip = [(p, '@' + p) for p in pars]

    PRODUCTS = ['HB', 'He-WD', 'CE', 'UK', 'failed', 'sdB', 'sdA'] + \
               ['stable', 'CE', 'contact', 'merger']
    MARKERS = ['square', 'triangle', 'asterisk', 'asterisk', 'diamond', 'circle', 'circle'] + \
              ['circle', 'diamond', 'square', 'triangle', ]
    COLORS = ['red', 'green', 'purple', 'purple', 'gray', 'blue', 'orange'] + \
             ['red', 'green', 'blue', 'gray']
    SIZES = [7, 7, 7, 7, 15, 7]

    v_func = """
        const norm = new Float64Array(xs.length)
        for (let i = 0; i < xs.length; i++) {
            if (xs[i] == 'sdB' || xs[i] == 'Fail' || xs[i] == 'CE') {
                    norm[i] = 15
            } else {
                    norm[i] = 7
            }
        }
        return norm
        """
    size_transform = mpl.CustomJSTransform(v_func=v_func)

    # Left Figure

    booleans = [True if val != 0 else False for val in source.data['G_HeCoreBurning']]
    view1 = CDSView(source=source, filters=[BooleanFilter(booleans)])

    p1 = figure(x_axis_label='Gaia BP-RP', y_axis_label='Gaia G mag', active_drag='box_select',
                tools=tools, tooltips=basic_tooltip, title="HeCoreBurning", y_range=(6,-5))

    p1.circle(hiparcos['bp_rp'], hiparcos['M_g'], size=1, color='gray')

    p1.scatter(x="BP-RP_HeCoreBurning", y="G_HeCoreBurning", source=source, fill_alpha=0.4,
               size=transform('z1', size_transform),
               color=factor_cmap('z1', COLORS, PRODUCTS),
               marker=factor_mark('z1', MARKERS, PRODUCTS),
               view=view1)

    # Right Figure

    booleans = [True if val != 0 else False for val in source.data['G_MLstart']]
    view2 = CDSView(source=source, filters=[BooleanFilter(booleans)])

    p2 = figure(x_axis_label='Gaia BP-RP', y_axis_label='Gaia G mag', active_drag='box_select',
                tools=tools, tooltips=basic_tooltip, title="ML start", y_range=(6,-5))

    p2.circle(hiparcos['bp_rp'], hiparcos['M_g'], size=1, color='gray')

    p2.scatter(x="BP-RP_MLstart", y="G_MLstart", source=source, fill_alpha=0.4,
               size=transform('z1', size_transform),
               color=factor_cmap('z1', COLORS, PRODUCTS),
               marker=factor_mark('z1', MARKERS, PRODUCTS),
               view=view2)

    plot = gridplot([[p1, p2]])

    # add interaction when selecting a model
    callback = CustomJS(args=dict(summary_source=source, table_source=table_source), code="""
                selected_indices = summary_source.selected.indices;

                console.log(summary_source.selected.indices[0]);
                console.log(summary_source);

                if (summary_source.selected.indices.length > 0){
                    var data = summary_source.data;
                    var ind = summary_source.selected.indices[0];
                    var parameters = table_source.data['parameters']
                    var values = table_source.data['values']

                    parameters.forEach(function (par, index) {
                        values[index] = data[par][ind];
                    });

                    //table_source.data['parameters'] = x;
                    table_source.data['values'] = values;

                    table_source.change.emit();
                }

                """)
    p1.js_on_event('tap', callback)
    p2.js_on_event('tap', callback)

    return plot, p1, p2


def make_HR_diagram(source):
    tools = "pan,wheel_zoom,box_zoom,box_select,hover,reset,crosshair"
    basic_tooltip = [("log_Teff", "$x{0.[000]}"), ("log_g", "$y{0.[000]}"), ("log_dt", "@log_dt{0.[000]}")]

    xpar = 'log_Teff'
    ypar = 'log_g'

    v_func = """
            const norm = new Float64Array(xs.length)
            for (let i = 0; i < xs.length; i++) {
                if (xs[i] < 0) {
                        norm[i] = 0
                } else {
                        norm[i] = xs[i]
                }
            }
            return norm
            """
    size_transform = mpl.CustomJSTransform(v_func=v_func)

    p = figure(plot_height=500, plot_width=500, tools=tools, title='HR diagram',
               x_axis_label=xpar, y_axis_label=ypar, tooltips=basic_tooltip)
    p.title.align = 'center'
    p.outline_line_width = 3
    p.outline_line_alpha = 0.3

    p.line(xpar, ypar, color='blue', source=source, legend_label='primary')
    p.circle(xpar, ypar, color='blue', source=source, size=transform('log_dt', size_transform), legend_label='primary')

    p.line(xpar+'_2', ypar+'_2', color='red', source=source, legend_label='secondary')
    p.circle(xpar+'_2', ypar+'_2', color='red', source=source, size=0, legend_label='secondary')

    p.patch([4.30, 4.60, 4.60, 4.30], [5, 5, 6.5, 6.5], alpha=0.3, color='blue', line_width=0)

    p.x_range.flipped = True
    p.y_range.flipped = True

    p.legend.location = "top_left"
    p.legend.click_policy = "hide"

    return p


def make_center_track(source):
    tools = "pan,wheel_zoom,box_zoom,box_select,hover,reset,crosshair"
    basic_tooltip = [("log_Rho_c", "$x{0.[000]}"), ("log_T_c", "$y{0.[000]}")]

    p = figure(plot_height=500, plot_width=500, tools=tools, title='Central properties',
                   x_axis_label='log_center_Rho', y_axis_label='log_center_T', tooltips=basic_tooltip)
    p.title.align = 'center'
    p.outline_line_width = 3
    p.outline_line_alpha = 0.3

    p.line('log_center_Rho', 'log_center_T', color='blue', source=source, legend_label='primary')
    p.circle('log_center_Rho', 'log_center_T', color='blue', source=source, size=0, legend_label='primary')

    p.line('log_center_Rho_2', 'log_center_T_2', color='red', source=source, legend_label='secondary')
    p.circle('log_center_Rho_2', 'log_center_T_2', color='red', source=source, size=0, legend_label='secondary')

    p.line(HIgnition['rho'], HeIgnition['T'], line_dash='dotted', color='black')
    p.line(HeIgnition['rho'], HeIgnition['T'], line_dash='dotted', color='black')
    p.line(OIgnition['rho'], OIgnition['T'], line_dash='dotted', color='black')
    p.line(edegeneracy['rho'], edegeneracy['T'], line_dash='dotted', color='black')

    h_label = mpl.Label(x=HIgnition['rho'][0], y=HeIgnition['T'][0], text='H',
                       render_mode='css', text_font_size='10pt')
    he_label = mpl.Label(x=HeIgnition['rho'][0], y=HeIgnition['T'][0], text='He', render_mode='css',
                        text_font_size='10pt', x_offset=5, y_offset=-5)
    o_label = mpl.Label(x=OIgnition['rho'][0], y=OIgnition['T'][0], text='O', render_mode='css',
                       text_font_size='10pt', x_offset=5, y_offset=-5)
    e_label = mpl.Label(x=edegeneracy['rho'][0], y=edegeneracy['T'][0], text='e-deg.', render_mode='css',
                       text_font_size='10pt', x_offset=5, y_offset=-5)

    p.add_layout(h_label)
    p.add_layout(he_label)
    p.add_layout(o_label)
    p.add_layout(e_label)

    p.legend.location = "top_left"
    p.legend.click_policy = "hide"

    return p


def make_summary_table(source):
    columns = [
        TableColumn(field="parameters", title="Parameter"),#, formatter=StringFormatter()),
        TableColumn(field="values", title="Value"),#, formatter=StringFormatter()),
    ]
    data_table = DataTable(source=source, columns=columns, width=400, height=600)

    return data_table


def make_history_plots(sources, pars_dict, labels=None):

    if len(sources) > 3:
        sources = sources[0:3]
    if labels is None:
        labels = [str(a) for a in list(range(1,4))]
    colors = Category10[3]

    x_range = None

    def make_figure(ypar, x_range):
        basic_tooltip = [("(x,y)", "($x{0.[00000]}, $y{0.[00000     ]})")]
        tools = "pan,wheel_zoom,box_zoom,box_select,hover,reset,crosshair"
        
        p = figure(plot_height=250, plot_width=500, tooltips=basic_tooltip, tools=tools, 
                   x_axis_label=pars_dict['x'], y_axis_label=pars_dict[ypar], x_range=None)

        for source, color, label in zip(sources, colors, labels):
            if len(sources) > 1:
                p.line('x', ypar, source=source, color=color, legend_label=label)
            else:
                p.line('x', ypar, source=source, color=color)
            p.circle('x', ypar, source=source, size=0)
        
        return p

    figures = {}
    topline = []
    for ypar in ['y1', 'y2', 'y3']:
        p = make_figure(ypar, x_range)
        x_range = p.x_range
        figures[ypar] = p
        topline.append(p)
        
        
    botline = []
    for ypar in ['y4', 'y5', 'y6']:
        p = make_figure(ypar, x_range)
        figures[ypar] = p
        botline.append(p)
    
    history_plots = gridplot([topline, botline])
    
    return history_plots, figures

def make_history_controls(track_sources, pars_dict, select_options, figures):
    
    calbackcode = """
        var parname = cb_obj.value;
        
        track_sources.forEach(function (source, index) {
            var data = source.data;
            data[axisname] = data[parname];
            source.change.emit();
        });
        
        history_pars[axisname] = parname; //store the parameter name in a global variable
        axis.axis_label = parname;
    """
    
    controls = {}
    xaxes = [figures['y'+str(i)].xaxis[0] for i in range(1,7)]
    x_callback = CustomJS(args=dict(track_sources=track_sources, axes=xaxes),code="""
        var parname = cb_obj.value;
        
        track_sources.forEach(function (source, index) {
            var data = source.data;
            data['x'] = data[parname];
            source.change.emit();
        });
        
        history_pars['x'] = parname; //store the parameter name in a global variable
        // loop over all x axes and update label
        axes.forEach(function (axis, index) {
            axis.axis_label = parname;
        });
        """)
    
    x1 = Select(title='X-Axis', value=pars_dict['x'], options=select_options)
    x1.js_on_change('value', x_callback)
    controls['x'] = x1
    
    for i in range(1,7):
        yc = Select(title='Y-Axis '+str(i), value=pars_dict['y'+str(i)], options=select_options)
        yc.js_on_change('value', CustomJS(args=dict(track_sources=track_sources, axisname='y'+str(i),
                                          axis=figures['y'+str(i)].yaxis[0]), code=calbackcode))
        
        controls['y'+str(i)] = yc
        
    # update_button = Button(label="Update", button_type="success")
    
    controls_c1 = widgetbox(controls['y1'], controls['y4'])
    controls_c2 = widgetbox(controls['y2'], controls['y5'])
    controls_c3 = widgetbox(controls['y3'], controls['y6'])
    controls_c4 = widgetbox(controls['x'])
    
    
    controls_history = row([Spacer(width=40, height=10), controls_c1, controls_c2, controls_c3, controls_c4])
    return controls_history


def make_comparison_plot(source, pars_dict, titles=['', '']):
    tools = "pan,wheel_zoom,box_zoom,box_select,tap,hover,reset,crosshair"

    pars = ['M1_init', 'M2_init', 'P_init', 'q_init', 'product', 'stability', 'termination_code']
    basic_tooltip = [(p, '@' + p) for p in pars]

    PRODUCTS = ['HB', 'He-WD', 'CE', 'UK', 'failed', 'sdB', 'sdA']
    MARKERS = ['square', 'triangle', 'asterisk', 'asterisk', 'diamond', 'circle', 'circle']
    COLORS = ['red', 'green', 'purple', 'purple', 'gray', 'blue', 'orange']
    SIZES = [7, 7, 7, 7, 15, 7]

    v_func = """
    const norm = new Float64Array(xs.length)
    for (let i = 0; i < xs.length; i++) {
        if (xs[i] == 'sdB' || xs[i] == 'Fail') {
                norm[i] = 15
        } else {
                norm[i] = 7
        }
    }
    return norm
    """
    size_transform = mpl.CustomJSTransform(v_func=v_func)

    # Left Figure

    p1 = figure(x_axis_label=pars_dict['x1'], y_axis_label=pars_dict['y1'], active_drag='box_select',
                tools=tools, title=titles[0])  # , tooltips=basic_tooltip)

    p1.scatter(x="x1", y="y1", source=source, fill_alpha=0.4,
               size=transform('product_1', size_transform),
               color=factor_cmap('product_1', COLORS, PRODUCTS),
               marker=factor_mark('product_1', MARKERS, PRODUCTS), )

    # Right Figure

    p2 = figure(x_axis_label=pars_dict['x2'], y_axis_label=pars_dict['y2'], active_drag='box_select',
                tools=tools, title=titles[1])  # , tooltips=basic_tooltip)

    p2.scatter(x="x2", y="y2", source=source, fill_alpha=0.4,
               size=transform('product_2', size_transform),
               color=factor_cmap('product_2', COLORS, PRODUCTS),
               marker=factor_mark('product_2', MARKERS, PRODUCTS), )

    # add interaction when selecting a model
    callback = CustomJS(args=dict(summary_source=source), code="""
                selected_indices = summary_source.selected.indices;
                """)
    p1.js_on_event('tap', callback)
    p2.js_on_event('tap', callback)

    plot = gridplot([[p1, p2]])

    return plot, p1, p2


def make_comparison_controls(source, track_sources, p1, p2, pars_dict, select_options):
    calbackcode = """
        var data = source.data;
        var parname = cb_obj.value;
        data[axisname+'1'] = data[parname+'_1'];
        data[axisname+'2'] = data[parname+'_2'];
        axis1.axis_label = parname;
        axis2.axis_label = parname;
        source.change.emit();
    """

    x1 = Select(title='X-Axis', value=pars_dict['x1'], options=select_options)
    x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x', axis1=p1.xaxis[0], axis2=p2.xaxis[0], suffix='_1'), code=calbackcode))

    y1 = Select(title='Y-Axis', value=pars_dict['y1'], options=select_options)
    y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='y', axis1=p1.yaxis[0], axis2=p2.yaxis[0], suffix='_1'), code=calbackcode))

    update_source = CustomJS(args=dict(summary_source=source, track_sources=track_sources, ), code="""
                        
            update_source(summary_source, track_sources[0], grid1, '_1')
            update_source(summary_source, track_sources[1], grid2, '_2')
            
            """)

    button = Button(label="Plot selected tracks", button_type="success", sizing_mode="stretch_width")
    button.js_on_click(update_source)

    controls = row([x1, y1, button])

    control_dict = {"x1": x1,
                    "y1": y1,
                    }

    return controls, control_dict