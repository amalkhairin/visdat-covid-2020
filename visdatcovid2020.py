#!/usr/bin/env python
# coding: utf-8

# !pip install geopandas

# !pip install geoplot

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


# The figure will be rendered in a static HTML file called output_file_test.html
output_file('tubes_output.html', 
            title='Statistik sebaran Covid-19 per provinsi di Indonesia')


# load dataset covid-19
df_cvdID = pd.read_csv("https://raw.githubusercontent.com/amalkhairin/JapaneseWhiskyReviewDataset/main/IDN-COVID19.csv")

# load dataset geojson yang berisi data gpd indonesia
id_gpd = gpd.read_file("https://raw.githubusercontent.com/Alf-Anas/batas-administrasi-indonesia/master/batas_provinsi/batas_provinsi.geojson")

# membersihkan data id_gpd agar sesuai dengan dataset covid-19
id_gpd["Provinsi"] = id_gpd["Provinsi"].str.title()
id_gpd["Provinsi"] = id_gpd["Provinsi"].str.replace("Dki Jakarta","DKI Jakarta")
id_gpd = id_gpd.sort_values("Provinsi", ascending=True, ignore_index=True)


# membuat fungsi yang akan memberikan level berdasarkan skala kasus terkonfirmasi
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


# fungsi untuk membersihkan dataset covid-19
def clear_data(df):
    # mengurutkan berdasarkan nama provinsi
    df = df.sort_values("Province_name", ascending=True, ignore_index=True)
    
    # membuat titik koordinat geometri
    splt = df["Features Geometry Coordinates"].str.split(",", n = 1, expand = True)
    df["x"] = pd.to_numeric(splt[0])
    df["y"] = pd.to_numeric(splt[1])
    
    #membuat kolom category untuk menyimpan data level hasil dari fungsi categorical_color_level
    df["category"] = [categorical_color_level(x) for x in df["Confirmed_cases"]]
    
    # drop kolom yang tidak diperlukan
    df.drop(["Features Geometry Coordinates"], axis=1, inplace=True)
    df.drop(["Type","Features Type","Features Geometry Type"], axis=1, inplace=True)
    
    # return dataset yang sudah dibersihkan
    return df


# menjalankan fungsi clear_data untuk membersihkan dataset covid-19
df_cvdID = clear_data(df_cvdID)

# df_cvdID.head(3)

# id_gpd.head(3)

# menambahkan atribut crs berupa kode epsg agar python dapat mengenalinya sebagai map
id_gpd.crs = {'init': 'epsg:23845'}


# fungsi json_data yang akan mengembalikan data json berdasarkan input nama provinsi
def json_data(selectedProvince):
    
    # menyimpan selectedProvince ke dalam variabel sp
    sp = selectedProvince
    
    #jika provinsi yang dipilih "None" maka mengembil seluruh data pada dataset dan data gpd
    if sp == 'None':
        df_dt = df_cvdID.copy()
        dt_gpd = id_gpd.copy()
    # jika tidak, maka hanya mengambil data sesuai dengan provinsi yang dipilih
    else:
        df_dt = df_cvdID[df_cvdID['Province_name'] == sp]
        dt_gpd = id_gpd[id_gpd['Provinsi'] == sp]
    
    # melakukan merge pada dataset dengan data gpd
    merge = dt_gpd.merge(df_dt,how='left', left_on=['Provinsi'], right_on=['Province_name'])

    # Convert to json
    merge_json = json.loads(merge.to_json())
    
    # Convert to json preferred string-like object
    json_data = json.dumps(merge_json)
    
    # return data json
    return json_data


# fungsi columndata akan mengembalikan sebuah data berdasarkan input provinsi
# berfungsi untuk tabel column yang akan ditampilkan pada layout
def columndata(selectedProvince):
    #menyimpan selected province pada variabel sp
    sp = selectedProvince
    
    # jika provinsi yang dipilih "None" maka mengambil seluruh data pada dataset covid-19
    if sp == 'None':
        column = df_cvdID.copy()
    #jika tidak maka mengambil data sesuai dengan input provinsi
    else:
        column = df_cvdID[df_cvdID['Province_name'] == sp]
    
    # mengurutkan berdasarkan jumlah comfirmed cases tertinggi ke terendah
    column=column.sort_values(by='Confirmed_cases', ascending=False)
    
    # membuat value rank untuk data column
    rank=[]
    for i in range(column.index.shape[0]):
        rank.append(i+1)
    
    # memasukkan kolom rank ke dataset
    column['rank']=rank
    most_cases=column.copy()
    
    # membuat dictionary yang berisi rank, nama provinsi, comfirmed cases, recovered cases, dan death cases
    source = dict(
        rank=[rank for rank in most_cases['rank']],
        province=[province for province in most_cases['Province_name']],
        confirmed=[confirmed for confirmed in most_cases['Confirmed_cases']],
        recovered=[recovered for recovered in most_cases['Recovered_cases']],
        death=[death for death in most_cases['Death_cases']]
    )
    return source


# funsgi update plot yang akan melakukan update pada plot jika terdapat input/perubahan
def update_plot(attr, old, new):
    # mengambil value dari menu dropdown
    province = menu.value
    # membuat data json baru berdasarkan value dari variabel province
    new_data = json_data(province)
    # membuat data geojson
    geosource.geojson = new_data
    # membuat data source baru untuk tabel berdasarkan value dari variabel province
    source.data = columndata(province)


# membuat list nama provinsi untuk dropdown menu
list_province_name = [i for i in df_cvdID['Province_name']]
list_province_name.insert(0,"None")

# membuat menu dropdown yang berisi nama-nama provinsi
menu = Select(
    options=list_province_name,
    value='None',
    title='Provinsi'
)
# melakukan set callback pada saat menu dropdown terdapat perubahan, plot akan di update
menu.on_change('value', update_plot)

# inisisalisasi data geosource dan source
geosource = GeoJSONDataSource(geojson = json_data("None"))
source = ColumnDataSource(columndata("None"))
    
# membuat color mapping
# factor list untuk factor mcolor mapping
factor_list = ['0','1 - 99','100 - 499','500 - 999','1.000 - 4.999','5.000 - 9.999','10.000 - 49.999','50.000 - 99.999','100.000 - 1.000.000', '> 1.000.000']

# palet warna yang akan digunakan
palet=['#242424', '#360007', '#67000d', '#cb181d', '#ef3b2c', '#fc9272', '#fcbba1', '#f7dada', '#fcf2f2', '#ffffff'] 
# membalik urutan warna menjadi yang tercerah ke tergelap
palet = palet[::-1]

# membuat color mapper menggunakan categorical color mapper
color_mapper = CategoricalColorMapper(factors= factor_list, palette=palet)

# membuat color bar yang akan ditampilkan pada layout figure
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


# setting figure
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

# melakukan reset view figure jika terdapat perubahan/update plot
js_reset = CustomJS(args=dict(figure=fig), code="figure.reset.emit()")
source.js_on_change('data', js_reset)

# jika terdapat perubahan pada geosource maka plot diupdate
geosource.on_change('selected', update_plot)

# membuat state patches yang berisi render map berdasarkan geosource dan color mapper
states=fig.patches(xs='xs',ys='ys', source = geosource,
                 fill_color = {'field' :'category', 'transform' : color_mapper},
                 line_color ='white', 
                 line_width = 0.5,
                 fill_alpha = 1)

# membuat label nama provinsi yang berada pada masing-masing provinsi pada map
labels = LabelSet(x='x', y='y',text='Province_name', text_align='center',x_offset=0, y_offset=0,
                  text_font_size='6pt',text_font_style='bold',
                  source = geosource, render_mode='canvas')

# menambahkan tools hover ke figue
fig.add_tools(HoverTool(renderers = [states],
                       tooltips = [ ('Provinsi','@Province_name'),
                                  ('Confirmed', '@Confirmed_cases'),
                                  ('Recovered', '@Recovered_cases'),
                                  ('Death', '@Death_cases')]))

# membuat tabel kolom untuk untuk menampikan provinsi dengan kasus tertinggi
columns = [
        TableColumn(field='rank', title='Rank'),
        TableColumn(field='province', title='Provinsi'),
        TableColumn(field='confirmed', title='Confirmed Case'),
        TableColumn(field='recovered', title='Recovered Case'),
        TableColumn(field='death', title='Death Case'),
    ]
tabel = DataTable(source=source, columns=columns,  width=440, height=540, index_position=None)

# menambahkan labels dan color bar ke layout figure
fig.add_layout(labels)
fig.add_layout(color_bar)

# Create layout and add to current document
layout = row(widgetbox(fig,menu),tabel)
curdoc().add_root(layout)