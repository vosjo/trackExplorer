 
#Load the packages
import pandas as pd
from flask import Flask, render_template, request
from bokeh.embed import components 
from bokeh.models import HoverTool

from bokeh.plotting import figure

#Connect the app
app = Flask(__name__)

#Get the data, from somewhere
df = pd.read_csv('http://www.astro.physik.uni-potsdam.de/~jorisvos/ModelData/BesanconLargeNew1.csv')

#Helper function
def get_plot(df, xpar, ypar):
    #Make plot and customize
    p = figure(x_axis_label=xpar, 
                y_axis_label=ypar, title='MESA models: BesanconLargeNew1')
    p.scatter(x=xpar, y=ypar, source=df )
    p.title.text_font_size = '16pt'
    #p.add_tools(HoverTool()) #Need to configure tooltips for a good HoverTool

    #Return the plot
    return(p)

@app.route('/')
def homepage():
    
    xpar = request.args.get("xpar")
    if xpar is None:
       xpar = df.columns[0]
    ypar = request.args.get("ypar")
    if ypar is None:
       ypar = df.columns[1]
      
    #Setup plot    
    p = get_plot(df, xpar, ypar)
    script, div = components(p)

    #Render the page
    return render_template('home.html', script=script, div=div, parameters=df.columns.values.tolist(),
                           current_xpar=xpar, current_ypar=ypar)    

if __name__ == '__main__':
    app.run(debug=True) #Set to false when deploying
