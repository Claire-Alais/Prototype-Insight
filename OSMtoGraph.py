"""
Read graphs in Open Street Maps osm format

Based on osm2graph.py by Karsten (K4r573n) from
https://github.com/k4r573n/OSM2Graph
Based on gistfile1.py by Abraham Flaxman from
https://gist.github.com/aflaxman/287370/
Based on osm.py from brianw's osmgeocode
http://github.com/brianw/osmgeocode, which is based on osm.py from
comes from Graphserver:
http://github.com/bmander/graphserver/tree/master and is copyright (c)
2007, Brandon Martin-Anderson under the BSD License
"""


import xml.sax
from xml.sax.saxutils import XMLGenerator
import copy
import networkx

import sys
import argparse
from urllib.request import urlopen  #added ".request", urllib.urlopen discontinued since python 2.6

import math
import urllib


verbose = 1
errors = 0


def vprint(stri,level):
    global verbose
    if verbose >= level:
        print(stri)

def getNetwork(left,bottom,right,top,transport="all"):
    """ Returns a filename to the downloaded data.
        down loads highways and public transport
    """
    bbox = "%f,%f,%f,%f"%(bottom,left,top,right)
    localfilename = "/tmp/input.osm"

    hw_query = ""
    if transport == "hw" or transport == "all":
        hw_query = ""+\
         "("+\
              "way("+bbox+")[highway];"+\
               ">;"+\
         ");"

    pt_query = ""
    if transport == "pt" or transport == "all":
        pt_query = ""+\
         "("+\
               "("+\
                   "relation("+bbox+")[type=route][route=tram];"+\
                   "relation("+bbox+")[type=route][route=bus];"+\
               ");"+\
               ">>;"+\
         ");"

       # pt_query = ""+\
       #  "("+\
       #        "("+\
       #             "relation[\"route_master\"=\"tram\"][\"network\"=\"VRB\"];"+\
       #        ");"+\
       #        ">>;"+\
       #  ");"
    meta = ""
    if (verbose >= 1):
        meta = " meta"

    api = "http://overpass-api.de/api/interpreter?data="
    url = ""+\
    "("+\
        hw_query+\
        pt_query+\
    ");"+\
    "out"+meta+";"

    vprint( api+url,2)

    url = api + urllib.quote(url)

    fp = urlopen( url )
    localFile = open(localfilename, 'w')
    localFile.write(fp.read())
    localFile.close()
    fp.close()
    return localfilename


# Node
#
# a class which represent a Openstreetmap-node as well as a graph vertex
class Node:
    def __init__(self, id, lon, lat):
        self.id = id
        self.lon = lon
        self.lat = lat
        self.tags = {}

    def checkTag(self,k,v):
        return k in self.tags and self.tags[k]==v


    # creats a osm-xml way object
    def toOSM(self,x,mark=False):
        # Generate SAX events
        frame = False
        if x == None :
            frame=True
            # Start Document
            x = XMLGenerator(sys.stdout, encoding="UTF-8")
            x.startDocument()
            x.startElement('osm',{"version":"0.6"})

        x.startElement('node',{"id":self.id, "lat":str(self.lat), "lon":str(self.lon), "visible":"true"})
        if mark:
            x.startElement('tag',{"k":'routing_crossing', "v":'yes'})
            x.endElement('tag')
        for k, v in self.tags.items():
            x.startElement('tag',{"k":k, "v":v})
            x.endElement('tag')
        x.endElement('node')
        if frame:
            x.endElement('osm')
            x.endDocument()
            
            
# Way
#
# a class which represent graph edges
# the ways includes split OSM-ways and PT-edges (between 2 stops)
class Way:
    def __init__(self, id, osm):
        self.osm = osm
        self.id = id
        self.nds = []
        self.tags = {}

    def split(self, dividers,ec):
        # slice the node-array using this nifty recursive function
        def slice_array(ar, dividers):
            for i in range(1,len(ar)-1):
                #try :
                    if dividers[ar[i]]>1:
                        #vprint( "slice at %s"%ar[i],2)
                        left = ar[:i+1]
                        right = ar[i:]
                    
                        rightsliced = slice_array(right, dividers)
                    
                        return [left]+rightsliced
                #except KeyError:
                    #continue
            return [ar]
            
        slices = slice_array(self.nds, dividers)
        
        # create a way object for each node-array slice
        ret = []
        for slice in slices:
            littleway = copy.copy( self )
            littleway.id += "-"+str(ec)
            littleway.nds = slice
            ret.append( littleway )
            ec += 1
            
        return ret

    # creates a osm-xml way object
    def toOSM(self,x):
        # Generate SAX events
        frame = False
        if x == None :
            frame=True
            # Start Document
            x = XMLGenerator(sys.stdout, encoding="UTF-8")
            x.startDocument()
            x.startElement('osm',{"version":"0.6"})

        x.startElement('way',{"id":"-"+self.id.split("-",2)[1]})
        
        #bad but for rendering ok
        #x.startElement('way',{"id":self.id.replace("special","").split("-",2)[0]})
        for nid in self.nds:
            x.startElement('nd',{"ref":nid})
            x.endElement('nd')
        for k, v in self.tags.items():
            if not(k=="name:ru"): #avoid cyrillic alphabet because UTF-8 does not like it
                x.startElement('tag',{"k":k, "v":v}) 
                x.endElement('tag')
        x.endElement('way')
        if frame:
            x.endElement('osm')
            x.endDocument()
            
            
# Relation
#
# equals to an OSM-Relation
class Relation:
    # only for relations with type=route
    def __init__(self, id, osm):
        self.osm = osm
        self.id = id
        # members are a hash in a list (to give them a order) with format
        # [idx]={id:role}
        self.mnode = []
        self.mway = []
        self.mrelation = []
        self.tags = {}

    # creates a osm-xml relation object
    def toOSM(self,x):
        # Generate SAX events
        frame = False
        if x == None :
            frame=True
            # Start Document
            x = XMLGenerator(sys.stdout, encoding="UTF-8") #added encoding=
            x.startDocument()
            x.startElement('osm',{"version":"0.6"})

        x.startElement('relation',{"id":"-"+self.id.split("-",2)[1]})
        
        #bad but for rendering ok
        #x.startElement('way',{"id":self.id.replace("special","").split("-",2)[0]})
        for nid,role in map(lambda t: (t.items()[0]), self.mnode):
            x.startElement('member',{"type":"node", "ref":nid, "role":role})
            x.endElement('member')
        for wid,role in map(lambda t: (t.items()[0]), self.mway):
            x.startElement('member',{"type":"way", "ref":wid, "role":role})
            x.endElement('member')
        for rid,role in map(lambda t: (t.items()[0]), self.mrelation):
            x.startElement('member',{"type":"relation", "ref":rid, "role":role})
            x.endElement('member')
        for k, v in self.tags.items():
            x.startElement('tag',{"k":k, "v":v})
            x.endElement('tag')
        x.endElement('way')
        if frame:
            x.endElement('osm')
            x.endDocument()
            
            
# Route
#
# filled by Route-Relations for buses and trams
class Route:
    # only for relations with type=route
    def __init__(self, id, osm):
        self.osm = osm
        self.id = id
        self.stops = []
        self.platforms = []
        self.ways = []
        self.tags = {}
        
        
# OSM
#
# class to handel all tasks
# reads OSM file
# parse the data
# provide export functionalities
class OSM:
    """ will parse a osm xml file and provide different export functions"""
    def __init__(self, filename_or_stream, transport):
        """ File can be either a filename or stream/file object."""
        vprint( "Start reading input...",2)
        nodes = {} # node objects
        ways = {}# way objects
        vways ={}# old ID: [list of new way IDs] to use relations
        relations = {} # relation objects
        
        superself = self

        # OSMHandler
        #
        # reads the OSM-file
        class OSMHandler(xml.sax.ContentHandler):
            @classmethod
            def setDocumentLocator(self,loc):
                pass
            
            @classmethod
            def startDocument(self):
                pass
                
            @classmethod
            def endDocument(self):
                pass
                
            @classmethod
            def startElement(self, name, attrs):
                if name=='node':
                    self.currElem = Node(attrs['id'], float(attrs['lon']), float(attrs['lat']))
                elif name=='way':
                    self.currElem = Way(attrs['id'], superself)
                elif name=='relation':
                    self.currElem = Relation(attrs['id'], superself)
                elif name=='tag':
                    self.currElem.tags[attrs['k']] = attrs['v']
                elif name=='nd':
                    self.currElem.nds.append( attrs['ref'] )
                elif name=='member':
                    if attrs['type']=='node':
                        self.currElem.mnode.append({attrs['ref']:attrs['role']})
                    elif attrs['type']=='way':
                        self.currElem.mway.append({attrs['ref'] : attrs['role']})
                    elif attrs['type']=='relation':
                        self.currElem.mrelation.append({attrs['ref']:attrs['role']})
                    #else:
                        #ignore it
                
            @classmethod
            def endElement(self,name):
                if name=='node':
                    nodes[self.currElem.id] = self.currElem
                elif name=='way':
                    ways[self.currElem.id] = self.currElem
                elif name=='relation':
                    relations[self.currElem.id] = self.currElem
                
            @classmethod
            def characters(self, chars):
                pass

        xml.sax.parse(filename_or_stream, OSMHandler)
        
        self.nodes = nodes
        self.ways = ways
        self.relations = relations

        # edge counter - to generate continues numbered new edge ids
        ec = 0

        vprint( "file reading finished",1)
        vprint( "\nnodes: "+str(len(nodes)),1)
        vprint( "ways: "+str(len(ways)),1)
        vprint( "relations: "+str(len(relations))+"\n",1)

            
        """ prepare ways for routing """
        #count times each node is used
        node_histogram = dict.fromkeys( self.nodes.keys(), 0 )
        for way in list(self.ways.values()):
            if len(way.nds) < 2:       #if a way has only one node, delete it out of the osm collection
                del self.ways[way.id]
            else:
                for node in way.nds:
                    #count public_transport=stop_position extra (to ensure a way split there)
                    if (transport=="all" or transport=="pt") and (\
                        nodes[node].checkTag('public_transport','stop_position') or 
                        nodes[node].checkTag('railway','tram_stop')):
                        node_histogram[node] += 2
                    else:
                        #try :
                            node_histogram[node] += 1
                        #except KeyError :
                            #continue

        
        #use that histogram to split all ways, replacing the member set of ways
        new_ways = {}
        for id, way in self.ways.items():   #problem with iteritems changed to items, iteritems deprecated
            split_ways = way.split(node_histogram,ec)
            ec += len(split_ways) #increase the counter 
            vways[way.id]=[]#lockup to convert old to new ids
            for split_way in split_ways:
                new_ways[split_way.id] = split_way
                vways[way.id].append(split_way.id)
        self.ways = new_ways
        self.vways = vways

        if not transport=="hw":
            self.addPublicTransport(ec)


    def checkPublicTransport(self):
        """ analyses which of the route relation is tagged correctly """
        routes = {}
        for r in self.relations.values():
            if not ('route' in r.tags and (r.tags['route']=='tram' or\
                    r.tags['route']=='bus')):
                continue

                # if stop number > = 2
# if number platform == number stops
# if all stops are nodes
# if all stops are at the beginning
# if stops and platforms are alternating

        return routes


    def addPublicTransport(self,ec):
        """ prepare route relations for routing """
        # error counter
        global errors
        
#TODO check if its well tagged before trying to add
        new_ways = {}
        for r in self.relations.values():
            if not ('route' in r.tags and (r.tags['route']=='tram' or\
                    r.tags['route']=='bus')):
                continue

            self.simplifyRoute(r)
            # parse this route and add the edges
            ec = self.route2edges(r, new_ways, ec)

        # add all new edges to the old ways
        vprint( "new and old ways",3)
        vprint( new_ways.keys(),3)
        vprint( self.ways.keys(),3)
        self.ways.update(new_ways)
        vprint( str(errors)+" Errors found\n",1)

    # substitutes all relation members by its' node and way members
    def simplifyRoute(self, rel, parent=None):
        
        vprint("simplify rel["+str(rel.id)+"] parent["+( str(parent.id) if
            parent != None else "")+"]",2);
        for subRelID,role in map(lambda t: (t.items()[0]), rel.mrelation):
            if 'route' in self.relations[subRelID].tags:
                # recursional calls
                self.simplifyRoute(self.relations[subRelID],rel)
#TODO delete the simplified relation out of the member list

        # add all nodes and ways to parent rel
        if parent != None:
            parent.mnode.extend(rel.mnode)
            parent.mway.extend(rel.mway)



    def route2edges(self, rel, new_ways, ec):
        # error counter
        global errors
        route_type = rel.tags['route']
        vprint( route_type,2)

        #extract stops
        stops = []
        #iterates through the items list (converted from hash)
        for nid,role in map(lambda t: t.items()[0], rel.mnode): 
            if role.split(':')[0]=='stop':
                stops.append(nid)
        vprint( str(len(stops))+" Stops found",2)

        tw = None
        # to turn the ways in the right direction
        last_node = None
        last_way = None
        i = 0
        #iterates through the items list (converted from hash)
        for old_wayid,role in map(lambda t: (t.items()[0]), rel.mway):
            if not (role=='forward' or role=='backward' or role==''):
                continue
            vprint( "\ntry adding Way["+str(old_wayid)+"]",2)
            vprint(self.vways[old_wayid],3)
            nds = []
            
            #first node out of first way
            fnode = self.ways[self.vways[old_wayid][0]].nds[0]

            #last node out of last way
            lnode = self.ways[self.vways[old_wayid][-1]].nds[-1]

            #check if node order is wrong
            invert = False
            if not last_node==None:
                if last_node==fnode:
                    invert = False
                elif last_node==lnode:
                    invert = True
                else:#ERROR
                    errors += 1
                    #idea to skip a route if an error was found
                    #TODO add this information to the check-report
                    vprint( "ERROR "+str(errors)+": Relation ["+str(rel.id)+"] in Way ["+str(old_wayid)+"] is not connected to the previous Way ["+str(last_way)+"]",0)
            else:
                invert = False

            last_way = old_wayid

            if invert:
                part_ways = self.vways[old_wayid][::-1]
                last_node = fnode
                vprint("invert way",2)
            else:
                part_ways = self.vways[old_wayid]
                last_node = lnode
                vprint("don't invert way",2)
            vprint( part_ways,3)

            #the next part hast to operate on the split ways
            for wayid in part_ways:
                if invert:
                    nds = self.ways[wayid].nds[::-1]
                else:
                    nds = self.ways[wayid].nds

                #skip if last stop was already reached
                if i>=len(stops):
                    break
                vprint( "waypart ["+str(wayid)+"] info: stop:"+str(i)+\
                        "["+stops[i]+"] \tn0: "+str(nds[0])+
                        "\tn-1:"+str(nds[-1]),2)
                #there are 2 different edges possible in kinds of stop position 0-x, 1-x
                #and it might be a continuing or the first edge
                if tw==None:
                    if stops[i]==nds[0]:
                        #its a new edge
                        tw = Way('special-'+str(ec),None) 
                        tw.tags = rel.tags;
                        tw.tags['highway']=route_type
                        tw.tags['oneway']="yes"#always oneway (one relation for each direction)
                        tw.nds.extend(nds) #all nodes have to belong to the edge cause way was split on stops

                        i += 1#jump to next stop_position
                        vprint( "create new Edge ["+str(tw.id)+"]",3)
                else:
                    if stops[i]==nds[0]:
                        #stop the last edge 
                        new_ways[tw.id] = tw
                        vprint("new wayid="+str(tw.id),3)
                        ec += 1

                        vprint( "finish edge ["+tw.id+"] and create new"+\
                                "Edge [special-"+str(ec)+"]",3)
                        #and start a new one
                        tw = Way('special-'+str(ec),None) 
                        tw.tags = rel.tags;
                        tw.tags['highway']= route_type
                        tw.tags['oneway']="yes"#always oneway (one relation for each direction)
                        tw.nds.extend(nds) #all nodes have to belong to the edge cause way was split on stops

                        i += 1#jump to next stop_position
                    else:
                        #just continue the last edge
                        tw.nds.extend(nds)
                        vprint( "continue Edge ["+str(tw.id)+"]",3)

        return ec
                        



    #calculates the way length in km
    # needs access to the nodes list - therefore its here
    def calclength(self,way):
        lastnode = None
        length = 0
        for node in way.nds:
            #try :
                if lastnode is None:

                    lastnode = self.nodes[node]
                    continue

                # copied from
                # http://stackoverflow.com/questions/5260423/torad-javascript-function-throwing-error
                R = 6371 # km
                dLat = (lastnode.lat - self.nodes[node].lat) * math.pi / 180
                dLon = (lastnode.lon - self.nodes[node].lon) * math.pi / 180
                lat1 = self.nodes[node].lat * math.pi / 180
                lat2 = lastnode.lat * math.pi / 180
                a = math.sin(dLat/2) * math.sin(dLat/2) + math.sin(dLon/2) * math.sin(dLon/2) * math.cos(lat1) * math.cos(lat2)
                c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
                d = R * c

                length += d

                lastnode = self.nodes[node]
            #except KeyError:
                #length = 1000 #or even Inf ? NaN ?
            

        return length


    # exports to osm xml
    def export(self,filename,transport):
        vprint( "osm-xml export...",1)

        #remember all nodes already exported
        unodes = {}

        fp = open(filename, "w")
        x = XMLGenerator(fp, "UTF-8")
        x.startDocument()
        x.startElement('osm',{"version":"0.6","generator":"crazy py script"})

        for w in self.ways.values():  #itervalues deprecated in python 3.0 --> changed to values
            if not 'highway' in w.tags:
                continue
            if transport == "all" or transport == "pt":
                if not (w.tags['highway']=='bus' or w.tags['highway']=='tram'):
                    continue
            if transport == "all" or transport == "hw":
                if (w.tags['highway']=='bus' or w.tags['highway']=='tram'):
                    continue
            w.toOSM(x)
            for nid in w.nds:
                if nid in unodes:#already used
                    continue
                unodes[nid]=True
                if w.nds.index(nid)==0 or w.nds.index(nid)==len(w.nds)-1:
                    #try:
                        self.nodes[nid].toOSM(x,True)
                    #except KeyError:
                        #continue
                else:
                    #try :
                        self.nodes[nid].toOSM(x)
                    #except KeyError:
                        #continue
        x.endElement('osm')
        x.endDocument()
    
    def exportCSV(self, filename_edges, filename_nodes):
        """
        will write into csv file, without header for now
        Header should be :
        source, target, length, car, bike, pedestrian, maxspeed
        """
        import csv
        vprint("csv export...",1)
        with open(filename_edges, "w", encoding='UTF8') as fe :
            ewriter = csv.writer(fe)
            ewriter.writerow(["source", "target", "length", "car", "bike", "pedestrian", "maxspeed"])
            count = 0
            for w in self.ways.values():
                if not 'highway' in w.tags:
                    continue
                #print(w.nds, w.tags, 'cycleway' in w.tags)
                count += 1
                lengthw = self.calclength(w)
                pedestrianw = pedestrian(w.tags['highway'])
                try :
                    maxspeedw = w.tags['maxspeed']
                except KeyError :
                    maxspeedw = None
                #first direction
                carw = car(w.tags['highway'])
                bikew = (carw and not(w.tags['highway'] in ['motorway', 'trunk', 'primary'])) or ('cycleway' in w.tags)
                ewriter.writerow([w.nds[0],w.nds[-1],lengthw, carw, bikew, pedestrianw, maxspeedw]) #TODO la suite
                #opposite direction
                carw = carw and (not('oneway' in w.tags) or w.tags['oneway']=='no')
                bikew = bikew and not('oneway:bicycle' in w.tags and w.tags['oneway:bicycle'] == 'yes')
                ewriter.writerow([w.nds[-1],w.nds[0],lengthw, carw, bikew, pedestrianw, maxspeedw])
                if count >3:
                    break
        vprint("Edge list done, starting node list...",1)
        with open(filename_nodes, "w", encoding='UTF8') as fn :
            nwriter = csv.writer(fn)
            nwriter.writerow(["Id", "Longitude", "Latitude"])
            count=0
            for n in self.nodes.values():
                nwriter.writerow([n.id, n.lon, n.lat])
                count += 1
                if count>10 :
                    break
        vprint("Export to csv done",1)

    # returns a nice graph
    # attention do not use for a bigger network (only single lines)
    def graph(self,only_roads=True):
        vprint('Beginning the graph within the function', 3)
        G = networkx.Graph()
        for w in self.ways.values():
            if only_roads and 'highway' not in w.tags:
                continue
            G.add_weighted_edges_from([(w.nds[0],w.nds[-1],self.calclength(w))])
        vprint('edges ok', 3)
        for n_id in list(G.nodes(data=True)):  #changes according to https://stackoverflow.com/questions/33734836/graph-object-has-no-attribute-nodes-iter-in-networkx-module-python
            #try :
                n = self.nodes[n_id[0]]  #changed from n_id to n_id[0]
                G.nodes[n_id[0]].update(dict(data=n))  #same + used .update()
            #except KeyError:
              #continue
        vprint('nodes ok', 3)
        return G
    
#    def graph2(self,only_roads=True):
#        vprint('Beginning the graph within the function', 3)
#        G = networkx.Graph()
#        for w in self.ways.values():
#            if only_roads and 'highway' not in w.tags:
#                continue
#            G.add_weighted_edges_from([(w.nds[0],w.nds[-1],self.calclength(w))])
#        vprint('edges ok', 3)
#        for n_id in list(G.nodes(data=True)):  #changes according to https://stackoverflow.com/questions/33734836/graph-object-has-no-attribute-nodes-iter-in-networkx-module-python
#            #try :
#                n = self.nodes[n_id[0]]  #changed from n_id to n_id[0]
#                G.nodes[n_id[0]].update(dict(data=n))  #same + used .update()
#            #except KeyError:
#              #continue
#        vprint('nodes ok', 3)
#        return G

#    def convert2neo4j(self,folder_to_put_db_in):
#        """export in neo4j db formart"""
        
        
        
# main
#
# method to read the command line arguments and run the program
#def main():
#    parser = argparse.ArgumentParser(\
#             description='This script provides you routeable data from the OpenStreetMap Project',
#             epilog="Have fun while usage")
#    #input selection
#    group = parser.add_mutually_exclusive_group()
#    group.add_argument('-f','--filename','--file', help='the path to a local file')
#    group.add_argument("-b", "--bbox", help="an area to download highways in the format 'left,bottom,right,top'")
#    parser.add_argument("-t", "--transport", choices=["all", "hw", "pt"], default="all",
#            help="Experimental Option! Uses as well public transportation information")
#    parser.add_argument("-o", "--osm-file", nargs='?', const='export.osm',
#            help="export the routeable graph as osm-xml to given file")
#            #type=argparse.FileType('w'),
#    parser.add_argument("-g", "--graph", help="saves the networkx graph obtained",
#                            dest="graph", action="store_true")
#    parser.add_argument("-w", "--floyd-warshall", help="compute the shortest path matrix with Floyd-Warshall",
#                            dest="paths", action="store_true")
#    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2, 3],
#                                help="increase output verbosity")
#    args = parser.parse_args()
#
#    #TODO ensure there is always an input - fix in argument syntax
#    #bbox or filename
#    global verbose
#    verbose = args.verbosity
#    if len(sys.argv) == 1:
#        parser.print_help()
#        sys.exit(0)
#
#    #get the input
#    fn = ""
#    if args.filename:
#        fn = args.filename
#
#    if args.bbox:
#        [left,bottom,right,top] = [float(x) for x in args.bbox.split(",")]
#        fn = getNetwork(left,bottom,right,top,args.transport)
#    if fn==None:
#        sys.exit("ERROR: no input given")
#
#    fp = open( fn,'r', encoding="UTF-8" )  #added encoding="UTF-u"
#    osm = OSM(fp,args.transport)
#    fp.close()
#
#    if args.osm_file:
#        vprint( "OSM-XML file export to '"+args.osm_file+"'",1)  
#        osm.export(args.osm_file,args.transport)
def pedestrian(highway):
    if highway in ['pedestrian', 'residential', 'living_street', 'tertiary', 'track', 'footway', 'bridleway', 'steps', 'corridor', 'path']:
        return True
    else :
        return False
    
def car(highway):
    if highway in ['residential', 'service', 'living_street', 'tertiary', 'track', 'motorway','primary','secondary','trunk','motorway_link','primary_link','secondary_link','trunk_link','tertiary_link']:
        return True
    else :
        return False

        
def main():
    parser = argparse.ArgumentParser(\
             description='This script provides you routeable data from the OpenStreetMap Project',
             epilog="Have fun while usage; OSMtoGraph.py -f map.osm -o -v 2")
    #input selection
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f','--filename','--file', help='the path to a local file')
    group.add_argument("-b", "--bbox", help="an area to download highways in the format 'left,bottom,right,top'")
    parser.add_argument("-t", "--transport", choices=["all", "hw", "pt"], default="all",
            help="Experimental Option! Uses as well public transportation information")
    parser.add_argument("-o", "--osm-file", nargs='?', const='export.osm',
            help="export the routeable graph as osm-xml to given file")
            #type=argparse.FileType('w'),
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2, 3],
                                help="increase output verbosity")
    parser.add_argument("-g", "--graph", help="saves the networkx graph",
                            dest="graph", action="store_true")
    parser.add_argument("-r", "--return_graph", help="returns the networkx graph",
                            dest="return_graph", action="store_true")
    parser.add_argument("-e", "--csv-edge-file", nargs='?', const='edge.csv',
            help="export the routeable graph as csv edgelist to given file, to use with -n")
    parser.add_argument("-n", "--csv-node-file", nargs='?', const='export.osm',
            help="export the routeable graph as csv node list to given file, to use with -e")
    args = parser.parse_args()

    global verbose
    verbose = args.verbosity
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(0)
        
    #get the input
    fn = ""
    if args.filename:
        fn = args.filename

    if args.bbox:
        [left,bottom,right,top] = [float(x) for x in args.bbox.split(",")]
        fn = getNetwork(left,bottom,right,top,args.transport)
    if fn==None:
        sys.exit("ERROR: no input given")
    
    main_function(fn, args.transport, args.osm_file, args.graph, verbose, args.return_graph, args.csv_edge_file, args.csv_node_file)


#if we want to use the traditional way of calling functions
def main_function(fn, transport="hw", osm_file=False, graph=False, verbose=verbose, return_graph=False, csv_edge_file=False, csv_node_file=False):
    print('I entered the main function')
    fp = open( fn,'r', encoding="utf-8" )  #added encoding="utf-u"
    osm = OSM(fp,transport)
    fp.close()

    if osm_file:
        vprint( "OSM-XML file export to '"+osm_file+"'",1)  
        osm.export(osm_file,transport)
        
    if csv_edge_file and csv_node_file:
        vprint("CSV file export to "+ csv_edge_file + " and " + csv_node_file,1 )
        osm.exportCSV(filename_edges = csv_edge_file, filename_nodes = csv_node_file)
        
    if graph or return_graph:
        vprint( "Convert as networkx graph",1)
        G=osm.graph()
        if graph :
            import save_module
            print('Graph will be saved as graph_nx')
            save_module.save_graph(G,'graph_nx')
        if return_graph :
            return G
        


if __name__ == '__main__':
    main()