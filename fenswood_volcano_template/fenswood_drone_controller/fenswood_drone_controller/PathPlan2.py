import geopandas as gpd
import pandas as pd
from shapely.geometry import point, Polygon
from haversine import haversine
import shapefile
import matplotlib
import mapclassify
import pyvisgraph as vg

Take_Off = (-2.6714965, 51.4234019)

# Flight Region
FR_A = (-2.6717208, 51.4234260)
FR_B = (-2.6701340, 51.4212462)
FR_C = (-2.6656878, 51.4224401)
FR_D = (-2.6670602, 51.4246918)

# No Fly Zone
NFZ_A = (-2.6720597, 51.4224669)
NFZ_B = (-2.6673723, 51.4235482)
NFZ_C = (-2.6670013, 51.4228490)
NFZ_D = (-2.6714016, 51.4217450)
No_Fly_Zone=(NFZ_A,NFZ_B,NFZ_C,NFZ_D)

# Area of interest
Area_of_Interest = (-2.6687656, 51.4219104)

# Outside area of interest annulus
Target1 = (-2.6684432, 51.4219778)

#for overlap
AB1=(-2.671951,51.423361)
AB2=(-2.666637,51.424813)
BC1=(-2.667174,51.425057)
BC2=(-2.665585,51.422312)
CD1=(-2.665397,51.422514)
CD2=(-2.670492,51.421145)
DA1=(-2.670029,51.421089)
DA2=(-2.671802,51.423564)

#points outside the flight boundary to create polygon
AB=(-2.669641, 51.424326)
BC=(-2.665659, 51.423752)
CD=(-2.667447, 51.421697)
DA=NFZ_A
#create polygon for flight region boundary
FR1=(AB1,AB2,AB)
FR2=(BC1,BC2,BC)
FR3=(FR_C,CD2,CD)
FR4=(DA1,DA2,DA)

def create_polygon(coordinates, polygon_name):
    polygon = Polygon(coordinates)
    gdf = gpd.GeoDataFrame(crs = {'init':'epsg:4326'})
    gdf.loc[0,'name'] = polygon_name
    gdf.loc[0, 'geometry'] = polygon
    return gdf

def get_waypoints():
    NFZpolygon = create_polygon(No_Fly_Zone, 'NFZ')
    FR1polygon = create_polygon(FR1, 'FR1')
    FR2polygon = create_polygon(FR2, 'FR2')
    FR3polygon = create_polygon(FR3, 'FR3')
    FR4polygon = create_polygon(FR4, 'FR4')
    
    Polygons=NFZpolygon.append(FR1polygon)
    Polygons=Polygons.append(FR2polygon)
    Polygons=Polygons.append(FR3polygon)
    Polygons=Polygons.append(FR4polygon)
    
    Polygons=Polygons.dissolve()
    
    Polygons.to_file("/ros_ws/src/fenswood_drone_controller/POLYGONS.shp")
    
    input_shapefile = shapefile.Reader("/ros_ws/src/fenswood_drone_controller/POLYGONS.shp")
    output_graphfile = "/ros_ws/src/fenswood_drone_controller/Polygons.graph"
    workers = 1  #cpu core to use
    
    shapes = input_shapefile.shapes()
    #print('The shapefile contains {} shapes.'.format(len(shapes)))
    
    polygons = []
    for shape in shapes:
        polygon = []
        for point in shape.points:
            polygon.append(vg.Point(point[0], point[1]))
        polygons.append(polygon)
        
    graph = vg.VisGraph()
    graph.build(polygons, workers=workers)
    
    graph.save(output_graphfile)
    
    start_point = vg.Point(Take_Off[0],Take_Off[1])
    end_point = vg.Point(Target1[0],Target1[1])
    
    graph = vg.VisGraph()
    graph.load("/ros_ws/src/fenswood_drone_controller/Polygons.graph")
    
    shortest_path = graph.shortest_path(start_point, end_point)
    
    path_distance = 0
    prev_point = shortest_path[0]
    for point in shortest_path[1:]:
        path_distance += haversine((prev_point.y, prev_point.x), (point.y, point.x))
        prev_point = point
        
    geopath = [[point.y, point.x] for point in shortest_path]
    
    # geomap  = folium.Map([0, 0], zoom_start=2)
    
#     for point in geopath:
#         folium.Marker(point, popup=str(point)).add_to(geomap)
#     folium.PolyLine(geopath).add_to(geomap)
    
#     folium.Marker(geopath[0], popup=str(start_point), icon=folium.Icon(color='red')).add_to(geomap)
#     folium.Marker(geopath[-1], popup=str(end_point), icon=folium.Icon(color='red')).add_to(geomap)
    
    # output_name = 'POLYGONS.html'
    # geomap.save(output_name)
    
    return geopath