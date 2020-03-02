 
#Load the packages
import pandas as pd
from flask import Flask, render_template, request

from bokeh.models import CustomJS, Select, Button, CheckboxGroup, ColumnDataSource
from bokeh.plotting import figure
from bokeh.layouts import gridplot, row, column, layout, widgetbox
from bokeh.embed import components

#Connect the app
app = Flask(__name__)

#Get the data, from somewhere
df = pd.read_csv('http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/BesanconLargeNew1.csv')
columns = df.columns.values.tolist()
df['x1'] = df['M1']
df['y1'] = df['qinit']
df['color1'] = df['Zinit']
df['x2'] = df['Zinit']
df['y2'] = df['Pinit_frac']
df['color2'] = df['M1']

source = ColumnDataSource(data=df)

#Helper function
def get_plot(source):
    #Make plot and customize
    p1 = figure()
    p1.scatter(x="x1", y="y1", source=source )
    
    p2 = figure()
    p2.scatter(x="x2", y="y2", source=source )
    
    plot = gridplot([[p1,p2]])

    #Return the plot
    return plot, p1, p2

def make_controls(source):
   
   calbackcode = """
    var data = source.data;
    var parname = cb_obj.value;
    data[axisname] = data[parname];
    source.change.emit();
   """
   
   x1 = Select(title='X-Axis 1', value='M1', options=columns)
   x1.js_on_change('value', CustomJS(args=dict(source=source, axisname='x1'), code=calbackcode))

   y1 = Select(title='Y-Axis 1', value='qinit', options=columns)
   y1.js_on_change('value', CustomJS(args=dict(source=source, axisname='y1'), code=calbackcode))

   color1 = Select(title='Color 1', value='Zinit', options=columns)
   #color.on_change('value', update)

   x2 = Select(title='X-Axis 2', value='Zinit', options=columns)
   x2.js_on_change('value', CustomJS(args=dict(source=source, axisname='x2'), code=calbackcode))

   y2 = Select(title='Y-Axis 2', value='Pinit_frac', options=columns)
   y2.js_on_change('value', CustomJS(args=dict(source=source, axisname='y2'), code=calbackcode))

   color2 = Select(title='Color 2', value='M1', options=columns)
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
    controls, control_dict = make_controls(source)
    
    #create layout
    top_plot = layout([[plot, controls]])
    
    
    script, div = components((top_plot))

    #Render the page
    return render_template('home.html', script=script, figure=div)    

if __name__ == '__main__':
    app.run(debug=True) #Set to false when deploying
