#!/usr/bin/env python
# coding: utf-8

# In[1]:


# !pip install geopandas


# In[2]:


# !pip install geoplot


# In[1]:


import pandas as pd
import geopandas as gpd
import geoplot.crs as gcrs
import geoplot as gplt
from shapely.geometry import Point
from bokeh.io import curdoc, output_notebook, output_file
from bokeh.plotting import figure, reset_output, show
from bokeh.models import HoverTool, ColumnDataSource, GeoJSONDataSource, CustomJS, LabelSet
from bokeh.models import CategoricalColorMapper, Dropdown, ColorBar, Patches, LinearColorMapper
from bokeh.models.widgets import DataTable, TableColumn
from bokeh.palettes import Spectral6
from bokeh.layouts import widgetbox, row, gridplot
from bokeh.models import Slider, Select
from bokeh.sampledata.sample_geojson import geojson
import bokeh.layouts
import json
import mapclassify as mc


# In[2]:


# The figure will be rendered in a static HTML file called output_file_test.html
output_file('tubes_output.html', 
            title='Statistik sebaran Covid-19 per provinsi di Indonesia')


# In[25]:


df_cvdID = pd.read_csv("https://raw.githubusercontent.com/amalkhairin/JapaneseWhiskyReviewDataset/main/IDN-COVID19.csv")
id_gpd = gpd.read_file("https://raw.githubusercontent.com/Alf-Anas/batas-administrasi-indonesia/master/batas_provinsi/batas_provinsi.geojson")

id_gpd["Provinsi"] = id_gpd["Provinsi"].str.title()
id_gpd["Provinsi"] = id_gpd["Provinsi"].str.replace("Dki Jakarta","DKI Jakarta")
id_gpd = id_gpd.sort_values("Provinsi", ascending=True, ignore_index=True)


# In[24]:

def categorical_color_level(x):
    if x == 0:
        return '0'
    elif x in range(1,99):
        return '1 - 99'
    elif x in range(100,499):
        return '100 - 499'
    elif x in range(500,999):
        return '500 - 999'
    elif x in range(1000,4999):
        return '1.000 - 4.999'
    elif x in range(5000,9999):
        return '5.000 - 9.999'
    elif x in range(10000,49999):
        return '10.000 - 49.999'
    elif x in range(50000,99999):
        return '50.000 - 99.999'
    elif x in range(100000,499999):
        return '100.000 - 1.000.000'
    else:
        return '> 1.000.000'

def clear_data(df):
    df = df.sort_values("Province_name", ascending=True, ignore_index=True)
    splt = df["Features Geometry Coordinates"].str.split(",", n = 1, expand = True)
    df["x"] = pd.to_numeric(splt[0])
    df["y"] = pd.to_numeric(splt[1])
    df["category"] = [categorical_color_level(x) for x in df["Confirmed_cases"]]
    df.drop(["Features Geometry Coordinates"], axis=1, inplace=True)
    df.drop(["Type","Features Type","Features Geometry Type"], axis=1, inplace=True)
    return df


# In[7]:


# def to_geodataframe(df):
#     df['coordinates'] = df[['x', 'y']].values.tolist()
#     df['coordinates'] = df['coordinates'].apply(Point)
#     df = gpd.GeoDataFrame(df, geometry='coordinates')
#     return df


# In[26]:


df_cvdID = clear_data(df_cvdID)
# df_cvdID = to_geodataframe(df_cvdID)


# In[27]:


df_cvdID.head(3)


# In[28]:


id_gpd.head(3)


# In[29]:


id_gpd.crs = {'init': 'epsg:23845'}


# In[34]:


def json_data(selectedDay):
    sd = selectedDay
    # Pull selected year
    if sd == 'None':
        df_dt = df_cvdID.copy()
        dt_gpd = id_gpd.copy()
    else:
        df_dt = df_cvdID[df_cvdID['Province_name'] == sd]
        dt_gpd = id_gpd[id_gpd['Provinsi'] == sd]
    
    merge = dt_gpd.merge(df_dt,how='left', left_on=['Provinsi'], right_on=['Province_name'])

    # Bokeh uses geojson formatting, representing geographical   features, with json
    # Convert to json
    merge_json = json.loads(merge.to_json())
    
    # Convert to json preferred string-like object 
    json_data = json.dumps(merge_json)
    return json_data


# In[41]:


def columndata(selectedDay):
    sd = selectedDay
    # Pull selected day
    if sd == 'None':
        column = df_cvdID.copy()
    else:
        column = df_cvdID[df_cvdID['Province_name'] == sd]
    column=column.sort_values(by='Confirmed_cases', ascending=False)
    rank=[]
    for i in range(column.index.shape[0]):
        rank.append(i+1)
    column['rank']=rank
    most_country=column.copy()
    source = dict(
        rank=[rank for rank in most_country['rank']],
        province=[province for province in most_country['Province_name']],
        confirmed=[confirmed for confirmed in most_country['Confirmed_cases']],
        recovered=[recovered for recovered in most_country['Recovered_cases']],
        death=[death for death in most_country['Death_cases']]
    )
    return source


# In[42]:


def update_plot(attr, old, new):
    day = menu.value
    new_data = json_data(day)
    geosource.geojson = new_data
    source.data = columndata(day)


# In[43]:


list_province_name = [i for i in df_cvdID['Province_name']]
list_province_name.insert(0,"None")
menu = Select(
    options=list_province_name,
    value='None',
    title='Provinsi'
)
menu.on_change('value', update_plot)

# In[45]:


geosource = GeoJSONDataSource(geojson = json_data("None"))
source = ColumnDataSource(columndata("None"))

# In[46]:
    
factor_list = ['0','1 - 99','100 - 499','500 - 999','1.000 - 4.999','5.000 - 9.999','10.000 - 49.999','50.000 - 99.999','100.000 - 1.000.000', '> 1.000.000']
palet=['#242424', '#360007', '#67000d', '#cb181d', '#ef3b2c', '#fc9272', '#fcbba1', '#f7dada', '#fcf2f2', '#ffffff'] 
palet = palet[::-1]

# color_mapper = LinearColorMapper(palette = palet, low = 0, high = 1000000)
color_mapper = CategoricalColorMapper(factors= factor_list, palette=palet)

color_bar = ColorBar(color_mapper=color_mapper, title='Confirmed Case',
                            #title=color.value.title(),
                            title_text_font_style='bold',
                            title_text_font_size='14px',
                            title_text_align='center',
                            orientation='vertical',
                            major_label_text_font_size='10px',
                            major_label_text_font_style='bold',
                            label_standoff=8,
                            major_tick_line_color='black',
                            major_tick_line_width=3,
                            major_tick_in=12,
                            location=(0,0))


# In[51]:


# Set up a generic figure() object
fig = figure(plot_height = 540 , plot_width = 900,
             toolbar_location = 'below',
             title='Statistik sebaran Covid-19 per provinsi di Indonesia',
             title_location='above',
             tools = ['pan, wheel_zoom, box_zoom, reset','tap'])

fig.title.text_font_size = '14pt'
fig.title.align = 'center'

fig.xaxis.visible = False
fig.yaxis.visible = False
fig.xgrid.grid_line_color = None
fig.ygrid.grid_line_color = None

js_reset = CustomJS(args=dict(figure=fig), code="figure.reset.emit()")
source.js_on_change('data', js_reset)
geosource.on_change('selected', update_plot)

states=fig.patches(xs='xs',ys='ys', source = geosource,
                 fill_color = {'field' :'category', 'transform' : color_mapper},
                 line_color ='white', 
                 line_width = 0.5,
                 fill_alpha = 1)

labels = LabelSet(x='x', y='y',text='Province_name', text_align='center',x_offset=0, y_offset=0,
                  text_font_size='6pt',text_font_style='bold',
                  source = geosource, render_mode='canvas')

fig.add_tools(HoverTool(renderers = [states],
                       tooltips = [ ('Provinsi','@Province_name'),
                                  ('Confirmed', '@Confirmed_cases'),
                                  ('Recovered', '@Recovered_cases'),
                                  ('Death', '@Death_cases')]))

columns = [
        TableColumn(field='rank', title='Rank'),
        TableColumn(field='province', title='Provinsi'),
        TableColumn(field='confirmed', title='Confirmed Case'),
        TableColumn(field='recovered', title='Recovered Case'),
        TableColumn(field='death', title='Death Case'),
    ]
tabel = DataTable(source=source, columns=columns,  width=440, height=540, index_position=None)

fig.add_layout(labels)
fig.add_layout(color_bar)

# layout = row(widgetbox(menu,tabel), fig)
layout = row(widgetbox(fig,menu),tabel)
# curdoc().add_root(row(fig,tabel))
curdoc().add_root(layout)

output_notebook()
# # # # # See what it looks like
show(layout)

