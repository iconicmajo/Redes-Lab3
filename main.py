"""
Universidad del Valle de Guatemala
Laboratorio 3 - Redes 
Authors:
    María José Castro
    Jennifer Sandoval
    María Inés Vásquez
Description:
    The following program aims to simulate the sending of messages using 
    the routing algorithms flooding, distance vector routing and link state routing
"""

import getpass
from networkx.algorithms.shortest_paths.generic import shortest_path
import yaml
from aioconsole import ainput
import networkx as nx
import asyncio
import logging
from datetime import datetime
import slixmpp
import networkx as nx
import random
from getpass import getpass
import sys

#Small fix that allows the program to run on windows operating systems due to an error with the asyncio library
if sys.platform == 'win32' and sys.version_info >= (3, 8):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

#Class that instantiates a client on an xmpp server
class Client(slixmpp.ClientXMPP):
    def __init__(self, jid, password, algoritmo, nodo, nodes, names, graph):
        super().__init__(jid, password)
        self.received = set()
        self.initialize(jid, password, algoritmo, nodo, nodes, names, graph)

        self.schedule(name="echo", callback=self.echo, seconds=10, repeat=True)
        self.schedule(name="update", callback=self.tree_update, seconds=10, repeat=True)
        
        # Handle events
        self.connected_event = asyncio.Event()
        self.presences_received = asyncio.Event()

        # Manage login and messages
        self.add_event_handler('session_start', self.start)
        self.add_event_handler('message', self.message)
        
        # Plugins
        self.register_plugin('xep_0030') # Service Discovery
        self.register_plugin('xep_0045') # Multi-User Chat
        self.register_plugin('xep_0199') # Ping


    # Client initialization
    async def start(self, event):
        self.send_presence() 
        await self.get_roster()
        self.connected_event.set()

    # Receiving messages
    async def message(self, msg):
        if msg['type'] in ('normal', 'chat'):
            await self.forward_msg(msg['body'])

    # This function can be used to forward your messages
    async def forward_msg(self, msg):
        message = msg.split('|')
        if message[0] == 'msg':
            #FLOODING ALGORITHM
            print('\nForwarding message... ')
            if self.algoritmo == '1':
                if message[2] == self.jid:
                    print("This message is for me >> " +  message[6])
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
                #DISTANCE VECTOR: SENT TO THE NEIGHBOR WITH THE SHORTEST DISTANCE
                print('\nUsing the distance vector algorithm')
                print(message)
                sendto= message[6].split('*')
                sendto = sendto[1].split('#')
                sendNode = sendto[1]
                
                for (p, d) in xmpp.graph.nodes(data=True):
                    if (p == sendNode):
                        jid_receiver = d['jid']
                print('Sending to: ', jid_receiver)

                if message[2] == self.jid:
                    print("This message is for me >> " +  message[6])
                else:
                    if message[3] != '0':
                        lista = message[4].split(",")
                        if self.nodo not in lista:
                            message[4] = message[4] + "," + str(self.nodo)
                            message[3] = str(int(message[3]) - 1)
                            StrMessage = "|".join(message)
                            self.send_message(
                                    mto=jid_receiver,
                                    mbody=StrMessage,
                                    mtype='chat' 
                                )  
                            print("Message sent")
                    else:
                        pass
            elif self.algoritmo == '3':
                # Link State Routing
                print('\nUsing the link state routing algorithm')
                # Forwarding state tables
                if message[2] == self.jid:
                    print("This message is for me >> " +  message[6])
                else:
                    if int(message[3]) > 0:
                        lista = message[4].split(",")
                        if self.nodo not in lista:
                            message[4] = message[4] + "," + str(self.nodo)
                            message[3] = str(int(message[3]) - 1)
                            StrMessage = "|".join(message)
                            target = []
                            # Adding information to state table
                            for x in self.graph.nodes().data():
                                if x[1]["jid"] == message[2]:
                                    target.append(x)
                            # Determining shortest path
                            shortest = nx.shortest_path(self.graph, source=self.nodo, target=target[0][0])
                            print('Path: ', shortest)
                            if len(shortest) > 0:
                                self.send_message(
                                    mto=self.names[shortest[1]],
                                    mbody=StrMessage,
                                    mtype='chat' 
                                )  
                    else:
                        pass
        elif message[0] == 'echo':
            #This function allows to know distance between adjacent nodes
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

    #Function that allows to store the updated information to the graph
    def tree_update(self):
        if self.algoritmo == '2':
            for i in self.nodes:
                self.graph.nodes[i]["neighbors"] = self.graph.neighbors(i)
            
            #update graph with new weights
            neigh = nx.graph.get_node_attributes(self.graph,'neighbors')

        elif self.algoritmo == '3':
            # Updating states table
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
    #initialization of the main arguments of the graph
    def initialize(self, jid, password, algoritmo, nodo, nodes, names, graph):
        self.algoritmo = algoritmo
        self.names = names
        self.graph = graph
        self.nodo = nodo
        self.nodes = nodes

#Data structure in which the network topology is stored
class Tree():
    """
   Class in which the tree of the user communication network is instantiated
    """
    def newTree(self, topo, names):
        G = nx.Graph()
        # Adding nodes
        for key, value in names["config"].items():
            G.add_node(key, jid=value)
            
        # Adding edges and assigning different weights
        for key, value in topo["config"].items():
            for i in value:
                weightA = random.uniform(0, 1)
                G.add_edge(key, i, weight=weightA)
        
        return G
    
# Function to manage the client
async def main(xmpp: Client):
    mainexecute = True
    origin = ""
    destiny = ""
    while mainexecute:
        choice = await ainput("Start chat (y: yes | n: no): ")
        if choice == 'y':
            to_user = await ainput("Enter the username of the user with whom you want to chat (name@alumchat.xyz)>>> ")
            active = True
            while active:
                mensaje = await ainput("Message >>> ")
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
                        # Relating node assignments to JID addresses
                        for (p, d) in xmpp.graph.nodes(data=True):
                            if (d['jid'] == xmpp.jid):
                                origin = p
                            if (d['jid'] == to_user):
                                destiny = p
                        # Getting the shortest path
                        shortest_path=nx.shortest_path(xmpp.graph, origin, destiny)
                        path=shortest_path
                        print("\nPath:")
                        print(path)
                        path.pop(0)
                        sendto = path[0]
                        mail = ""
                        for (p, d) in xmpp.graph.nodes(data=True):
                            if (p == sendto):
                                mail = d['jid']

                        print("\nSending to: "+mail)

                        # Only adding remaining nodes to the message
                        nei = '#'.join(str(e) for e in path)
                        mensaje = mensaje+"*"+nei
                        xmpp.send_message(
                            mto=mail,
                            mbody=mensaje,
                            mtype='chat' 
                        )

                    elif (xmpp.algoritmo == '3'):
                        target=[]
                        for x in xmpp.graph.nodes().data():
                            if x[1]["jid"] == to_user:
                                target.append(x)
                        mensaje = "msg|" + str(xmpp.jid) + "|" + str(to_user) + "|" + str(xmpp.graph.number_of_nodes()) + "||" + str(xmpp.nodo) + "|" + str(mensaje)
                        # Getting the shortest path
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
    Main function where the topography and user name for the network is read and loaded.
    communication and the user selects the routing algorithm to use
    for message forwarding
    """
    lector_topo = open("topo.txt", "r", encoding="utf8")
    lector_names = open("names.txt", "r", encoding="utf8")
    topo_string = lector_topo.read()
    names_string = lector_names.read()
    topo = yaml.load(topo_string, Loader=yaml.FullLoader)
    names = yaml.load(names_string, Loader=yaml.FullLoader)

    # Entering user information
    jid = input("User (name@alumchat.xyz)>>> ")
    pswd = getpass("Password >>> ")
    alg = input("Select routing algorithm (Flooding >> 1 | Distance vector routing >> 2 | Link state routing >> 3): ") 

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
    