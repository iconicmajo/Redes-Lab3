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
import yaml
import networkx as nx
import matplotlib.pyplot as plt
import asyncio
import logging
from aioconsole import aprint
from datetime import datetime
import slixmpp
import networkx as nx

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
        #self.schedule(name="update", callback=self.update_message, seconds=15, repeat=True)
        
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
            #await aprint("\n{}".format(msg['body']))
            await self.reply_message(msg['body'])

    # Esta funcion la pueden usar para reenviar sus mensajes
    async def reply_message(self, msg):
        #await aprint(msg)
        message = msg.split('|')
        #await aprint(message)
        if message[0] == '1':
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
                pass
            elif self.algoritmo == '3':
                pass
        elif message[0] == '2':
            print('Este es el metodo de update')
            if self.algoritmo == '2':
                pass
            elif self.algoritmo == '3':
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
                # await aprint("La diferencia es de: ", difference)
                self.graph.nodes[message[5]]['distance'] = difference
                # print(self.graph.nodes.data())
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
        if self.algoritmo == '2':
                pass
        elif self.algoritmo == '3':
            pass

class Tree():
    def newTree(self, topo, names):
        G = nx.Graph()
        #agregar nodo
        for key, value in names["config"].items():
            G.add_node(key, jid=value)
            
        #agregar vertice
        for key, value in topo["config"].items():
            for i in value:
                G.add_edge(key, i)
        
        return G
    
# Funcion para manejar el cliente
async def main(xmpp: Client):
    corriendo = True
    while corriendo:
        print(""" ACCIÓN A TOMAR: 
        0. Mensajeria
        1. Salir
        """)
        opcion = await ainput("¿Qué acción deseas realizar?: ")
        if opcion == '0':
            destinatario = await ainput("¿A quién? ")
            activo = True
            while activo:
                mensaje = await ainput("Mensaje... ")
                if (len(mensaje) > 0):
                    if xmpp.algoritmo == '1':
                        mensaje = "1|" + str(xmpp.jid) + "|" + str(destinatario) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        for i in xmpp.nodes:
                            xmpp.send_message(
                                mto=xmpp.names[i],
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
    alg = input("Ingrese el algoritmo seleccionado (Flooding > 1): ") 

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
    