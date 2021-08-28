"""
María José Castro
Jennifer Sandoval
María Inés Vásquez
Laboratorio 3
"""

import logging
import getpass
from aioconsole.stream import aprint
from optparse import OptionParser
from aioconsole import ainput
from networkx.algorithms.shortest_paths.generic import shortest_path
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import asyncio
import logging
from aioconsole import aprint
from datetime import datetime
import slixmpp
import networkx as nx
import random
import sys

if sys.platform == 'win32' and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, algoritmo, nodo, nodes, names, graph):
        super().__init__(jid, password)
        self.received = set()
        self.initialize(jid, password, algoritmo, nodo, nodes, names, graph)

        self.schedule(name="echo", callback=self.echo, seconds=10, repeat=True)
        self.schedule(name="update", callback=self.tree_update, seconds=10, repeat=True)
        
        # Manejar los eventos
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        # Manejar inicio de sesion y mensajes
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        
        # Plugins
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # Ping


    #Inicialización de cliente
    async def start(self, event):
        self.send_presence() 
        await self.get_roster()
        self.connected_event.set()

    # Convo con usuarios
    async def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            await self.forward_msg(msg['body'])

    # Esta funcion la pueden usar para reenviar sus mensajes
    async def forward_msg(self, msg):
        message = msg.split('|')
        if message[0] == 'msg':
            #FLOODING ALGORITHM
            print('ENTRO A REENVIAR MENSAJE')
            if self.algoritmo == '1':
                if message[2] == self.jid:
                    print("Este mensaje es para mi >> " +  message[6])
                else:
                    if message[3] != '0':
                        lista = message[4].split(",")
                        if self.nodo not in lista:
                            message[4] = message[4] + "," + str(self.nodo)
                            message[3] = str(int(message[3]) - 1)
                            StrMessage = "|".join(message)
                            for i in self.nodes:
                                self.send_message(
                                    mto=self.names[i],
                                    mbody=StrMessage,
                                    mtype='chat' 
                                )  
                    else:
                        pass
            elif self.algoritmo == '2':
                #DISTANCE VECTOR: SE LE MANDA AL VECINO CON DISTANCIA MÁS CORTA
                """print('Este es el metodo de reenviar de distance vector')
                print(message)"""
                sendto= message[6].split('*')
                #sendto= message[7].split('*')
                #sendto = sendto[1].split('#')
                print('MANDAR A: ', sendto)
                if message[2] == self.jid:
                    print("Este mensaje es para mi >> " +  message[6])
                else:
                    print("ENTRA A ESTO QUE YO QUIERO QUE ENTRE")
                    if message[3] != '0':
                        print("ENTRA A ESTO QUE YO QUIERO QUE ENTRE X2")
                        lista = message[4].split(",")
                        if self.nodo not in lista:
                            message[4] = message[4] + "," + str(self.nodo)
                            message[3] = str(int(message[3]) - 1)
                            StrMessage = "|".join(message)
                            #for i in self.nodes:
                            self.send_message(
                                    mto=sendto[0],
                                    mbody=StrMessage,
                                    mtype='chat' 
                                )  
                            print("LO MANDA")
                    else:
                        pass
            elif self.algoritmo == '3':
            #Reenvio de paquetes para link state route utilizando flooding (En vez de que envie un mensaje tiene que mandar la tabla de estado)
                if message[2] == self.jid:
                    print("Este mensaje es para mi >> " +  message[6])
                else:
                    if int(message[3]) > 0:
                        lista = message[4].split(",")
                        if self.nodo not in lista:
                            message[4] = message[4] + "," + str(self.nodo)
                            message[3] = str(int(message[3]) - 1)
                            StrMessage = "|".join(message)
                            target = []
                            for x in self.graph.nodes().data():
                                if x[1]["jid"] == message[2]:
                                    target.append(x)
                            shortest = nx.shortest_path(self.graph, source=self.nodo, target=target[0][0])
                            if len(shortest) > 0:
                                self.send_message(
                                    mto=self.names[shortest[1]],
                                    mbody=StrMessage,
                                    mtype='chat' 
                                )  
                    else:
                        pass
        elif message[0] == 'echo':
            if message[6] == '':
                now = datetime.now()
                timestamp = datetime.timestamp(now)
                mensaje = msg + str(timestamp)
                self.send_message(
                            mto=message[1],
                            mbody=mensaje,
                            mtype='chat' 
                        )
            else:
                difference = float(message[6]) - float(message[4])
                self.graph.nodes[message[5]]['weight'] = difference
        else:
            pass

    def echo(self):
        for i in self.nodes:
            mensaje = "echo|" + str(self.jid) + "|" + str(self.names[i]) + "||"+ str(datetime.timestamp(datetime.now())) +"|" + str(i) + "|"
            self.send_message(
                        mto=self.names[i],
                        mbody=mensaje,
                        mtype='chat' 
                    )

    def tree_update(self):
        if self.algoritmo == '2':
            for i in self.nodes:
                self.graph.nodes[i]["neighbors"] = self.graph.neighbors(i)
            
            #update graph with new weights
            neigh = nx.graph.get_node_attributes(self.graph,'neighbors')

        elif self.algoritmo == '3':
            for x in self.graph.nodes().data():
                if x[0] in self.nodes:
                    dataneighbors= x
            for x in self.graph.edges.data('weight'):
                if x[1] in self.nodes and x[0]==self.nodo:
                    dataedges = x
            StrNodes = str(dataneighbors) + "-" + str(dataedges)
            for i in self.nodes:
                update_msg = "2|" + str(self.jid) + "|" + str(self.names[i]) + "|" + str(self.graph.number_of_nodes()) + "||" + str(self.nodo) + "|" + StrNodes
                self.send_message(
                        mto=self.names[i],
                        mbody=update_msg,
                        mtype='chat' 
                    )

    def initialize(self, jid, password, algoritmo, nodo, nodes, names, graph):
        self.algoritmo = algoritmo
        self.names = names
        self.graph = graph
        self.nodo = nodo
        self.nodes = nodes

class Tree():
    """
    Clase en la cual se instancia arbol de la red de comunicación de usuarios
    """
    def newTree(self, topo, names):
        G = nx.Graph()
        #agregar nodo
        for key, value in names["config"].items():
            G.add_node(key, jid=value)
            
        #agregar vertice
        for key, value in topo["config"].items():
            for i in value:
                weightA = random.uniform(0, 1)
                G.add_edge(key, i, weight=weightA)
        
        return G
    
# Funcion para manejar el cliente
async def main(xmpp: Client):
    mainexecute = True
    origin = ""
    secuencia = 0
    destiny = ""
    while mainexecute:
        choice = await ainput("¿Deseas abrir una conversación? (y: sí | n: o): ")
        if choice == 'y':
            to_user = await ainput("¿A quién? (name@alumchat.xyz)>>> ")
            active = True
            #shortest_path=nx.shortest_path(xmpp.graph, origin, destiny)
            #path=shortest_path
            while active:
                """print("ESTE ES EL ALG")
                print(xmpp.algoritmo)"""
                mensaje = await ainput("Mensaje >>> ")
                if (len(mensaje) > 0):
                    if (xmpp.algoritmo == '1'):
                        mensaje = "msg|" + str(xmpp.jid) + "|" + str(to_user) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        for i in xmpp.nodes:
                            xmpp.send_message(
                                mto=xmpp.names[i],
                                mbody=mensaje,
                                mtype='chat' 
                            )  
                    elif (xmpp.algoritmo == '2'):
                        
                        mensaje = "msg|" + str(xmpp.jid) + "|" + str(to_user) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        graph = xmpp.graph
                        for (p, d) in xmpp.graph.nodes(data=True):
                            if (d['jid'] == xmpp.jid):
                                origin = p
                            if (d['jid'] == to_user):
                                destiny = p
                        

                        shortest_path=nx.shortest_path(xmpp.graph, origin, destiny)
                        path=shortest_path
                        #mensaje = "msg|" + str(xmpp.jid) + "|" + str(to_user) + "|" + str(len(shortest_path)) + "||" + str(shortest_path) + "|" +str('distancia')+"|"+ str(mensaje)
                        print("ESTE ES EL PATH")
                        print(path)
                        #No se esta eliminando el primer elemento :(
                        path.pop(0)
                        sendto = path[0]
                        mail = ""
                        for (p, d) in xmpp.graph.nodes(data=True):
                            #print(p,d)
                            if (p == sendto):
                                mail = d['jid']

                        print("A ESTE SE LO MANDO: "+mail)

                                
                        nei = '#'.join(str(e) for e in path)
                        mensaje = mensaje+"*"+nei
                        #print(mensaje)
                        xmpp.send_message(
                            mto=mail,
                            mbody=mensaje,
                            mtype='chat' 
                        )
                    #print("A VER SI ENTRA")

                    elif (xmpp.algoritmo == '3'):
                        target=[]
                        for x in xmpp.graph.nodes().data():
                            if x[1]["jid"] == to_user:
                                target.append(x)
                        """print("target"*25)
                        print(target)"""
                        mensaje = "msg|" + str(xmpp.jid) + "|" + str(to_user) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        shortest = nx.shortest_path(xmpp.graph, source=xmpp.nodo, target=target[0][0])
                        if len(shortest) > 0:
                            xmpp.send_message(
                                mto=xmpp.names[shortest[1]],
                                mbody=mensaje,
                                mtype='chat' 
                            )
                        
                            


                    else:
                        xmpp.send_message(
                            mto=to_user,
                            mbody=mensaje,
                            mtype='chat' 
                        )
        elif choice == 'n':
            mainexecute = False
            xmpp.disconnect()
        else:
            pass


if __name__ == "__main__":
    """
    Main donde se lee y carga la topografía y nombre de usuarios para red de 
    comunicación y el usuario selecciona el algoritmo de enrutamiento ha utilizar 
    para el reenvío de mensajes
    """
    lector_topo = open("topo.txt", "r", encoding="utf8")
    lector_names = open("names.txt", "r", encoding="utf8")
    topo_string = lector_topo.read()
    names_string = lector_names.read()
    topo = yaml.load(topo_string, Loader=yaml.FullLoader)
    names = yaml.load(names_string, Loader=yaml.FullLoader)

    #introducción de información de usuario
    jid = input("Usuario (name@alumchat.xyz)>>> ")
    pswd = input("Contraseña>>> ")
    alg = input("Algoritmo de enrutamiento seleccionado (Flooding >> 1 | Distance vector routing >> 2 | Link state routing >> 3): ") 

    tree = Tree()

    for key, value in names["config"].items():
            if jid == value:
                nodo = key
                nodes = topo["config"][key]

    graph = tree.newTree(topo, names)
    xmpp = Client(jid, pswd, alg, nodo, nodes, names["config"], graph)
    xmpp.connect() 
    xmpp.loop.run_until_complete(xmpp.connected_event.wait())
    xmpp.loop.create_task(main(xmpp))
    xmpp.process(forever=False)
    