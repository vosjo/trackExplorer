
from bokeh import models as mpl
from bokeh.models import CustomJS, Select, Button, CheckboxGroup
from bokeh.transform import linear_cmap, factor_cmap, factor_mark, transform
from bokeh.palettes import Spectral11, Set1, Category10, Dark2, Inferno256, RdBu
from bokeh.plotting import figure
from bokeh.layouts import gridplot, row, column, layout, widgetbox, Spacer


def make_summary_plot(source, pars_dict):
    
    cmin, cmax = 0, 1
    cpallet = Dark2[8]
    
    PRODUCTS = ['HB', 'He-WD', 'CE', 'failed', 'sdB']
    MARKERS = ['square', 'triangle', 'asterisk', 'diamond', 'circle']
    SIZES = [7, 7, 7, 7, 15]
    
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
    
    p1 = figure(x_axis_label=pars_dict['x1'], y_axis_label=pars_dict['y1'])
    
    color_mapper = mpl.LinearColorMapper(cpallet, low=cmin, high=cmax)
    
    p1.scatter(x="x1", y="y1", source=source, fill_alpha=0.4,
            size=transform('product', size_transform),
            color={'field': 'color1', 'transform': color_mapper},
            marker=factor_mark('product', MARKERS, PRODUCTS),)
    
    color_bar1 = mpl.ColorBar(color_mapper=color_mapper, location=(0,0), title=pars_dict['color1'], title_text_font_size='12pt')
    p1.add_layout(color_bar1, 'right')
    
    # Right Figure
    
    p2 = figure(x_axis_label=pars_dict['x2'], y_axis_label=pars_dict['y2'])
    
    color_mapper = mpl.LinearColorMapper(cpallet, low=cmin, high=cmax)
    
    p2.scatter(x="x2", y="y2", source=source, fill_alpha=0.4,
            size=transform('product', size_transform),
            color={'field': 'color2', 'transform': color_mapper},
            marker=factor_mark('product', MARKERS, PRODUCTS),)
    
    color_bar2 = mpl.ColorBar(color_mapper=color_mapper, location=(0,0), title=pars_dict['color2'], title_text_font_size='12pt')
    p2.add_layout(color_bar2, 'right')
    
    plot = gridplot([[p1,p2]])
    
    return plot, p1, p2


def make_summary_controls(source, p1, p2, pars_dict, select_options):

    calbackcode = """
        var data = source.data;
        var parname = cb_obj.value;
        data[axisname] = data[parname];
        axis.axis_label = parname;
        source.change.emit();
    """

    x1 = Select(title='X-Axis 1', value=pars_dict['x1'], options=select_options)
    x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x1', axis=p1.xaxis[0]), code=calbackcode))

    y1 = Select(title='Y-Axis 1', value=pars_dict['y1'], options=select_options)
    y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='y1', axis=p1.yaxis[0]), code=calbackcode))

    color1 = Select(title='Color 1', value=pars_dict['color1'], options=select_options)
    y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='color1', axis=None), code=calbackcode))

    x2 = Select(title='X-Axis 2', value=pars_dict['x2'], options=select_options)
    x2.js_on_change('value', CustomJS(args=dict(source=source, axisname='x2', axis=p2.xaxis[0]), code=calbackcode))

    y2 = Select(title='Y-Axis 2', value=pars_dict['y2'], options=select_options)
    y2.js_on_change('value', CustomJS(args=dict(source=source, axisname='y2', axis=p2.yaxis[0]), code=calbackcode))

    color2 = Select(title='Color 2', value=pars_dict['color2'], options=select_options)
    #color2.on_change('value', update)

    button = Button(label="Plot selected", button_type="success")
    #button.on_click(plot_selected_history)


    # create sumary plots
    controls1 = widgetbox(x1, y1, color1, width=300)
    controls2 = widgetbox(x2, y2, color2, width=300)
    controls = column([controls1, controls2, button])

    control_dict = {"x1": x1,
                    "y1": y1,
                    "color1": color1,
                    "x2": x2,
                    "y2": y2,
                    "color2": color2,
                    }

    return controls, control_dict


def make_history_plots(source, pars_dict):
    
    def make_figure(ypar):
        basic_tooltip = [("(x,y)", "($x{0.[00000]}, $y{0.[00000     ]})")]
        tools = "pan,wheel_zoom,box_zoom,box_select,hover,reset,crosshair"
        
        p = figure(plot_height=250, plot_width=500, tooltips=basic_tooltip, tools=tools, 
                   x_axis_label=pars_dict['x'], y_axis_label=pars_dict[ypar]) 
        
        p.line('x', ypar, source=source)
        p.circle('x', ypar, source=source, size=0)
        
        return p
        
    topline = []
    for ypar in ['y1', 'y2', 'y3']:
        p = make_figure(ypar)
        topline.append(p)
        
        
    botline = []
    for ypar in ['y4', 'y5', 'y6']:
        p = make_figure(ypar)
        botline.append(p)
    
    history_plots = gridplot([topline, botline])
    
    return history_plots

def make_history_controls(source, pars_dict, select_options):
    
    calbackcode = """
        var data = source.data;
        var parname = cb_obj.value;
        data[axisname] = data[parname];
        source.change.emit();
    """
    
    controls = {}
    
    x1 = Select(title='X-Axis', value=pars_dict['x'], options=select_options)
    x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x'), code=calbackcode))
    controls['x'] = x1
    
    for i in range(1,7):
        yc = Select(title='Y-Axis '+str(i), value=pars_dict['y'+str(i)], options=select_options)
        yc.js_on_change('value', CustomJS(args=dict(source=source, axisname='y'+str(i)), code=calbackcode))
        
        controls['y'+str(i)] = yc
        
    update_button = Button(label="Update", button_type="success")
    
    controls_c1 = widgetbox(controls['y1'], controls['y4'])
    controls_c2 = widgetbox(controls['y2'], controls['y5'])
    controls_c3 = widgetbox(controls['y3'], controls['y6'])
    controls_c4 = widgetbox(controls['x'], update_button)
    
    
    controls_history = row([Spacer(width=40, height=10), controls_c1, controls_c2, controls_c3, controls_c4])
    return controls_history
    
