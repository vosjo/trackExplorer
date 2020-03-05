
from bokeh import models as mpl
from bokeh.models import CustomJS, Select, Button, CheckboxGroup
from bokeh.transform import linear_cmap, factor_cmap, factor_mark, transform
from bokeh.plotting import figure
from bokeh.layouts import gridplot, row, column, layout, widgetbox, Spacer

from pathlib import Path
import pandas as pd

base_path = Path(__file__).parent

# boundaries
edegeneracy = pd.read_csv(base_path / 'plot_info/kap_rad_cond_eq.data', sep='\s+', names=['rho', 'T'])
HIgnition = pd.read_csv(base_path / 'plot_info/hydrogen_burn.data', sep='\s+', names=['rho', 'T'])
HeIgnition = pd.read_csv(base_path / 'plot_info/helium_burn.data', sep='\s+', names=['rho', 'T'])
OIgnition = pd.read_csv(base_path / 'plot_info/carbon_burn.data', sep='\s+', names=['rho', 'T'])


def make_summary_plot(source, pars_dict):
    
    tools = "pan,wheel_zoom,box_zoom,box_select,tap,hover,reset,crosshair"
    
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
    
    p1 = figure(x_axis_label=pars_dict['x1'], y_axis_label=pars_dict['y1'], active_drag='box_select', tools=tools)
    
    p1.scatter(x="x1", y="y1", source=source, fill_alpha=0.4,
            size=transform('product', size_transform),
            color=factor_cmap('product', COLORS, PRODUCTS),
            marker=factor_mark('product', MARKERS, PRODUCTS),)
    
    # color_bar1 = mpl.ColorBar(color_mapper=color_mapper, location=(0,0), title=pars_dict['color1'], title_text_font_size='12pt')
    # p1.add_layout(color_bar1, 'right')

    # Right Figure
    
    p2 = figure(x_axis_label=pars_dict['x2'], y_axis_label=pars_dict['y2'], active_drag='box_select', tools=tools)
    
    p2.scatter(x="x2", y="y2", source=source, fill_alpha=0.4,
            size=transform('product', size_transform),
            color=factor_cmap('product', COLORS, PRODUCTS),
            marker=factor_mark('product', MARKERS, PRODUCTS),)
    
    # color_bar2 = mpl.ColorBar(color_mapper=color_mapper, location=(0,0), title=pars_dict['color2'], title_text_font_size='12pt')
    # p2.add_layout(color_bar2, 'right')

    plot = gridplot([[p1,p2]])
    
    # add interaction when selecting a model
    callback = CustomJS(args=dict(source=source), code="""selected_indices = source.selected.indices;""")
    p1.js_on_event('tap', callback)
    p2.js_on_event('tap', callback)
    
    return plot, p1, p2


def make_summary_controls(source, history_source, p1, p2, pars_dict, select_options):

    calbackcode = """
        var data = source.data;
        var parname = cb_obj.value;
        data[axisname] = data[parname];
        summary_pars[axisname] = parname; //store the parameter name in a global variable
        axis.axis_label = parname;
        source.change.emit();
    """

    x1 = Select(title='X-Axis 1', value=pars_dict['x1'], options=select_options)
    x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x1', axis=p1.xaxis[0]), code=calbackcode))

    y1 = Select(title='Y-Axis 1', value=pars_dict['y1'], options=select_options)
    y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='y1', axis=p1.yaxis[0]), code=calbackcode))

    # color1 = Select(title='Color 1', value=pars_dict['color1'], options=select_options)
    # y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='color1', axis=None), code=calbackcode))

    x2 = Select(title='X-Axis 2', value=pars_dict['x2'], options=select_options)
    x2.js_on_change('value', CustomJS(args=dict(source=source, axisname='x2', axis=p2.xaxis[0]), code=calbackcode))

    y2 = Select(title='Y-Axis 2', value=pars_dict['y2'], options=select_options)
    y2.js_on_change('value', CustomJS(args=dict(source=source, axisname='y2', axis=p2.yaxis[0]), code=calbackcode))

    # color2 = Select(title='Color 2', value=pars_dict['color2'], options=select_options)
    #color2.on_change('value', update)

    update_source = CustomJS(args=dict(summary_source=source, history_source=history_source), code="""
        if (selected_indices.length == 0){
            filename = '';
        } else {
            filename = summary_source.data['filename'][selected_indices[0]];
        }
        
        $.ajax({
        url : "/history", 
        type : "POST",
        data: JSON.stringify({
        filename: filename,
        history_pars: history_pars,
        }),
        dataType: "json",
        success : function(json) {
            console.log(json)
            console.log(history_source.data)
            
            for (var key in json) {
                history_source.data[key] = new Float64Array(json[key])
            }
            
            console.log(history_source.data)
            history_source.change.emit();
        },
        error : function(xhr,errmsg,err) {
            console.log(xhr.status + ": " + xhr.responseText);
        },
        }); 
        """)
    
    button = Button(label="Plot selected", button_type="success")
    button.js_on_click(update_source)


    # create sumary plots
    controls1 = widgetbox(x1, y1, width=300)
    controls2 = widgetbox(x2, y2, width=300)
    controls = column([controls1, controls2, button])

    control_dict = {"x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2,
                    }

    return controls, control_dict

def make_HR_diagram(source):
    tools = "pan,wheel_zoom,box_zoom,box_select,hover,reset,crosshair"

    xpar = 'log_Teff'
    ypar = 'log_g'

    p = figure(plot_height=500, plot_width=500, tools=tools, title='HR diagram',
               x_axis_label=xpar, y_axis_label=ypar)
    p.title.align = 'center'
    p.outline_line_width = 3
    p.outline_line_alpha = 0.3

    p.line(xpar, ypar, color='blue', source=source, legend_label='primary')
    p.circle(xpar, ypar, color='blue', source=source, size=0, legend_label='primary')

    p.line(xpar+'_2', ypar+'_2', color='red', source=source, legend_label='secondary')
    p.circle(xpar+'_2', ypar+'_2', color='red', source=source, size=0, legend_label='secondary')

    p.x_range.flipped = True
    p.y_range.flipped = True

    p.legend.location = "top_left"
    p.legend.click_policy = "hide"

    return p

def make_center_track(source):

    tools = "pan,wheel_zoom,box_zoom,box_select,hover,reset,crosshair"

    p = figure(plot_height=500, plot_width=500, tools=tools, title='Central properties',
                   x_axis_label='log_center_Rho', y_axis_label='log_center_T')
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

def make_history_plots(source, pars_dict):
    
    def make_figure(ypar):
        basic_tooltip = [("(x,y)", "($x{0.[00000]}, $y{0.[00000     ]})")]
        tools = "pan,wheel_zoom,box_zoom,box_select,hover,reset,crosshair"
        
        p = figure(plot_height=250, plot_width=500, tooltips=basic_tooltip, tools=tools, 
                   x_axis_label=pars_dict['x'], y_axis_label=pars_dict[ypar]) 
        
        p.line('x', ypar, source=source)
        p.circle('x', ypar, source=source, size=0)
        
        return p

    figures = {}
    topline = []
    for ypar in ['y1', 'y2', 'y3']:
        p = make_figure(ypar)
        figures[ypar] = p
        topline.append(p)
        
        
    botline = []
    for ypar in ['y4', 'y5', 'y6']:
        p = make_figure(ypar)
        figures[ypar] = p
        botline.append(p)
    
    history_plots = gridplot([topline, botline])
    
    return history_plots, figures

def make_history_controls(source, pars_dict, select_options, figures):
    
    calbackcode = """
        var data = source.data;
        var parname = cb_obj.value;
        data[axisname] = data[parname];
        history_pars[axisname] = parname; //store the parameter name in a global variable
        axis.axis_label = parname;
        source.change.emit();
    """
    
    controls = {}
    
    x1 = Select(title='X-Axis', value=pars_dict['x'], options=select_options)
    x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x'), code=calbackcode))
    controls['x'] = x1
    
    for i in range(1,7):
        yc = Select(title='Y-Axis '+str(i), value=pars_dict['y'+str(i)], options=select_options)
        yc.js_on_change('value', CustomJS(args=dict(source=source, axisname='y'+str(i), axis=figures['y'+str(i)].yaxis[0]),
                                          code=calbackcode))
        
        controls['y'+str(i)] = yc
        
    # update_button = Button(label="Update", button_type="success")
    
    controls_c1 = widgetbox(controls['y1'], controls['y4'])
    controls_c2 = widgetbox(controls['y2'], controls['y5'])
    controls_c3 = widgetbox(controls['y3'], controls['y6'])
    controls_c4 = widgetbox(controls['x'])
    
    
    controls_history = row([Spacer(width=40, height=10), controls_c1, controls_c2, controls_c3, controls_c4])
    return controls_history
    
