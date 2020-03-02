 
#Load the packages
import pandas as pd
from flask import Flask, render_template, request

from bokeh import models as mpl
from bokeh.models import CustomJS, Select, Button, CheckboxGroup, ColumnDataSource
from bokeh.transform import linear_cmap, factor_cmap, factor_mark, transform
from bokeh.palettes import Spectral11, Set1, Category10, Dark2, Inferno256, RdBu
from bokeh.plotting import figure
from bokeh.layouts import gridplot, row, column, layout, widgetbox
from bokeh.embed import components

#Connect the app
app = Flask(__name__)

#Get the data, from somewhere
df = pd.read_csv('http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/BesanconLargeNew1.csv')
columns = df.columns.values.tolist()

start_pars = {'x1': 'M1',
              'y1': 'qinit',
              'color1': 'FeHinit',
              'x2': 'Zinit', 
              'y2': 'Pinit_frac',
              'color2': 'M1',
            }

df['x1'] = df[start_pars['x1']]
df['y1'] = df[start_pars['y1']]
df['color1'] = df[start_pars['color1']]
df['x2'] = df[start_pars['x2']]
df['y2'] = df[start_pars['y2']]
df['color2'] = df[start_pars['color2']]

source = ColumnDataSource(data=df)

#Helper function
def get_plot(source):
    
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
    
    p1 = figure(x_axis_label=start_pars['x1'], y_axis_label=start_pars['y1'])
    
    color_mapper = mpl.LinearColorMapper(cpallet, low=cmin, high=cmax)
    
    p1.scatter(x="x1", y="y1", source=source, fill_alpha=0.4,
               size=transform('product', size_transform),
               color={'field': 'color1', 'transform': color_mapper},
               marker=factor_mark('product', MARKERS, PRODUCTS),)
    
    color_bar1 = mpl.ColorBar(color_mapper=color_mapper, location=(0,0), title=start_pars['color1'], title_text_font_size='12pt')
    p1.add_layout(color_bar1, 'right')
    
    # Right Figure
    
    p2 = figure(x_axis_label=start_pars['x2'], y_axis_label=start_pars['y2'])
    
    color_mapper = mpl.LinearColorMapper(cpallet, low=cmin, high=cmax)
    
    p2.scatter(x="x2", y="y2", source=source, fill_alpha=0.4,
               size=transform('product', size_transform),
               color={'field': 'color2', 'transform': color_mapper},
               marker=factor_mark('product', MARKERS, PRODUCTS),)
    
    color_bar2 = mpl.ColorBar(color_mapper=color_mapper, location=(0,0), title=start_pars['color2'], title_text_font_size='12pt')
    p2.add_layout(color_bar2, 'right')
    
    plot = gridplot([[p1,p2]])
    
    return plot, p1, p2

def make_controls(source, p1, p2):
   
   calbackcode = """
    var data = source.data;
    var parname = cb_obj.value;
    data[axisname] = data[parname];
    axis.axis_label = parname;
    source.change.emit();
   """
   
   x1 = Select(title='X-Axis 1', value=start_pars['x1'], options=columns)
   x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x1', axis=p1.xaxis[0]), code=calbackcode))

   y1 = Select(title='Y-Axis 1', value=start_pars['y1'], options=columns)
   y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='y1', axis=p1.yaxis[0]), code=calbackcode))

   color1 = Select(title='Color 1', value=start_pars['color1'], options=columns)
   y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='color1', axis=None), code=calbackcode))

   x2 = Select(title='X-Axis 2', value=start_pars['x2'], options=columns)
   x2.js_on_change('value', CustomJS(args=dict(source=source, axisname='x2', axis=p2.xaxis[0]), code=calbackcode))

   y2 = Select(title='Y-Axis 2', value=start_pars['y2'], options=columns)
   y2.js_on_change('value', CustomJS(args=dict(source=source, axisname='y2', axis=p2.yaxis[0]), code=calbackcode))

   color2 = Select(title='Color 2', value=start_pars['color2'], options=columns)
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


@app.route('/')
def homepage():
      
    #Setup plot    
    plot, p1, p2 = get_plot(source)
    controls, control_dict = make_controls(source, p1, p2)
    
    #create layout
    top_plot = layout([[plot, controls]])
    
    
    script, div = components((top_plot))

    #Render the page
    return render_template('home.html', script=script, figure=div)    

if __name__ == '__main__':
    app.run(debug=True) #Set to false when deploying
