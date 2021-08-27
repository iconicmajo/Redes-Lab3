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

"""if sys.platform == 'win32' and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())"""


class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, algoritmo, nodo, nodes, names, graph):
        super().__init__(jid, password)
        self.received = set()
        self.algoritmo = algoritmo
        # self.topo = topo
        self.names = names
        self.graph = graph
        # Cambio en vez de recibir toda la red recibe su nodo y nodos asociados
        self.nodo = nodo
        self.nodes = nodes
        # self.nodos = nodos
        self.schedule(name="echo", callback=self.echo_message, seconds=10, repeat=True)
        self.schedule(name="update", callback=self.update_message, seconds=10, repeat=True)
        
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


    # Iniciar sesion
    async def start(self, event):
        self.send_presence() 
        await self.get_roster()
        self.connected_event.set()

    # Recibir mensajes
    async def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            await self.reply_message(msg['body'])

    # Esta funcion la pueden usar para reenviar sus mensajes
    async def reply_message(self, msg):
        #await aprint(msg)
        message = msg.split('|')
        #await aprint(message)

        if message[0] == '1':
            #FLOODING ALGORITHM
            print('Este es el metodo de reenviar')
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
                    #print("ENTRA A ESTO QUE YO QUIERO QUE ENTRE")
                    if message[3] != '0':
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
                            target = [x for x in self.graph.nodes().data() if x[1]["jid"] == message[2]]
                            shortest = nx.shortest_path(self.graph, source=self.nodo, target=target[0][0])
                            if len(shortest) > 0:
                                self.send_message(
                                    mto=self.names[shortest[1]],
                                    mbody=StrMessage,
                                    mtype='chat' 
                                )  
                    else:
                        pass
        elif message[0] == '2':
            #print('Este es el metodo de update')
            if self.algoritmo == '2':
                pass
            elif self.algoritmo == '3':
                # Utilizar flooding para para verificar que el numero de saltos sea mayor a 0 
                # que el mensaje no ha pasado por este nodo
                if int(message[3]) > 0:
                    lista = message[4].split(",")
                    if self.nodo not in lista:
                        message[4] = message[4] + "," + str(self.nodo)
                        message[3] = str(int(message[3]) - 1)
                        esquemaRecibido = message[6]
                        StrMessage = "|".join(message)
                        # Mi esquema de mis vecinos
                        dataneighbors = [x for x in self.graph.nodes().data() if x[0] in self.nodes]
                        dataedges = [x for x in self.graph.edges.data('weight') if x[1] in self.nodes and x[0]==self.nodo]
                        StrNodes = str(dataneighbors) + "-" + str(dataedges)
                        for i in self.nodes:
                            update_msg = "2|" + str(self.jid) + "|" + str(self.names[i]) + "|" + str(self.graph.number_of_nodes()) + "||" + str(self.nodo) + "|" + StrNodes
                            # Reenviar mensaje recibido del update del vecino
                            self.send_message(
                                mto=self.names[i],
                                mbody=StrMessage,
                                mtype='chat' 
                            )
                            # Enviar mi update de mis vecinos  
                            self.send_message(
                                    mto=self.names[i],
                                    mbody=update_msg,
                                    mtype='chat' 
                                )
                        
                        # Actualizar tabla
                        # print(esquemaRecibido)
                        divido = esquemaRecibido.split('-')
                        nodos = ast.literal_eval(divido[0])
                        aristas = ast.literal_eval(divido[1])
                        # print(nodos)
                        # print(aristas)
                        self.graph.add_nodes_from(nodos)
                        self.graph.add_weighted_edges_from(aristas)
                        # print(self.graph.edges.data())
                else:
                    pass
        elif message[0] == '3':
            #print('Este es el metodo de echo')
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

    def echo_message(self):
        #print("schedule prueba echo")
        for i in self.nodes:
            # print(self.names[i])
            now = datetime.now()
            timestamp = datetime.timestamp(now)
            mensaje = "3|" + str(self.jid) + "|" + str(self.names[i]) + "||"+ str(timestamp) +"|" + str(i) + "|"
            self.send_message(
                        mto=self.names[i],
                        mbody=mensaje,
                        mtype='chat' 
                    )

    def update_message(self):
        
        print("schedule prueba update")
        if self.algoritmo == '2':
            for i in self.nodes:
                """for j in self.graph.neighbors(i):
                    print(j)"""
                self.graph.nodes[i]["neighbors"] = self.graph.neighbors(i)
            
            #for n in self.graph.nodes:
            neigh = nx.graph.get_node_attributes(self.graph,'neighbors')

        elif self.algoritmo == '3':
            # Tipo | Nodo fuente | Nodo destino | Saltos | Distancia | Listado de nodos | Mensaje
            # Esquema de mis vecinos
            #print("ENTRA AL 3")
            dataneighbors = [x for x in self.graph.nodes().data() if x[0] in self.nodes]
            dataedges = [x for x in self.graph.edges.data('weight') if x[1] in self.nodes and x[0]==self.nodo]
            StrNodes = str(dataneighbors) + "-" + str(dataedges)
            #print(StrNodes)
            for i in self.nodes:
                update_msg = "2|" + str(self.jid) + "|" + str(self.names[i]) + "|" + str(self.graph.number_of_nodes()) + "||" + str(self.nodo) + "|" + StrNodes
                self.send_message(
                        mto=self.names[i],
                        mbody=update_msg,
                        mtype='chat' 
                    )

class Tree():
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
    corriendo = True
    origin = ""
    secuencia = 0
    destiny = ""
    while corriendo:
        print(""" ACCIÓN A TOMAR: 
        0. Mensajeria
        1. Salir
        """)
        opcion = await ainput("¿Qué acción deseas realizar?: ")
        if opcion == '0':
            destinatario = await ainput("¿A quién? ")
            activo = True
            #shortest_path=nx.shortest_path(xmpp.graph, origin, destiny)
            #path=shortest_path
            while activo:
                """print("ESTE ES EL ALG")
                print(xmpp.algoritmo)"""
                mensaje = await ainput("Mensaje... ")
                if (len(mensaje) > 0):
                    if (xmpp.algoritmo == '1'):
                        mensaje = "1|" + str(xmpp.jid) + "|" + str(destinatario) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        for i in xmpp.nodes:
                            xmpp.send_message(
                                mto=xmpp.names[i],
                                mbody=mensaje,
                                mtype='chat' 
                            )  
                    elif (xmpp.algoritmo == '2'):
                        
                        mensaje = "1|" + str(xmpp.jid) + "|" + str(destinatario) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        graph = xmpp.graph
                        for (p, d) in xmpp.graph.nodes(data=True):
                            if (d['jid'] == xmpp.jid):
                                origin = p
                            if (d['jid'] == destinatario):
                                destiny = p
                        

                        shortest_path=nx.shortest_path(xmpp.graph, origin, destiny)
                        path=shortest_path
                        #mensaje = "1|" + str(xmpp.jid) + "|" + str(destinatario) + "|" + str(len(shortest_path)) + "||" + str(shortest_path) + "|" +str('distancia')+"|"+ str(mensaje)
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
                        #print("AQUI ANDO Y SÍ ENTRA")
                        #Creando la tabla de estado
                        """table_state=[]
                        secuencia=secuencia+1
                        table_state.append(xmpp.jid)
                        table_state.append(secuencia)   
                        table_state.append(xmpp.nodes) 
                        print('PROBANDOO')
                        print(table_state)
                        for i in xmpp.nodes:
                            print('entro al ciclo'+ str(i) )
                            xmpp.send_message(
                                    mto=xmpp.names[i],
                                    mbody=str(table_state),
                                    mtype='chat' 
                                )"""
                        target = [x for x in xmpp.graph.nodes().data() if x[1]["jid"] == destinatario]
                        mensaje = "1|" + str(xmpp.jid) + "|" + str(destinatario) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        shortest = nx.shortest_path(xmpp.graph, source=xmpp.nodo, target=target[0][0])
                        if len(shortest) > 0:
                            xmpp.send_message(
                                mto=xmpp.names[shortest[1]],
                                mbody=mensaje,
                                mtype='chat' 
                            )
                        
                            


                    else:
                        xmpp.send_message(
                            mto=destinatario,
                            mbody=mensaje,
                            mtype='chat' 
                        )
        elif opcion == '1':
            corriendo = False
            xmpp.disconnect()
        else:
            pass


if __name__ == "__main__":
    lector_topo = open("topo.txt", "r", encoding="utf8")
    lector_names = open("names.txt", "r", encoding="utf8")
    topo_string = lector_topo.read()
    names_string = lector_names.read()
    topo = yaml.load(topo_string, Loader=yaml.FullLoader)
    names = yaml.load(names_string, Loader=yaml.FullLoader)

    #introducción de parámetros
    jid = input("Ingrese su nombre de usuario: ")
    pswd = input("Ingrese su contraseña: ")
    alg = input("Ingrese el algoritmo seleccionado (Flooding >> 1 | Distance vector routing >> 2 | Link state routing >> 3): ") 

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
    