import asyncio
import html
import os
from dataclasses import dataclass
from typing import Any, Union, cast
import numpy as np
from nano_vectordb import NanoVectorDB
import inspect




#  import package.common.utils as utils


from lightrag.utils import load_json, logger, write_json
from ..base import (
    BaseGraphStorage
)
from neo4j import GraphDatabase
# Replace with your actual URI, username, and password
URI = "neo4j://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "your_password"
# Create a driver object


@dataclass
class GraphStorage(BaseGraphStorage):
    @staticmethod
    def load_nx_graph(file_name):
       print ("no preloading of graph with neo4j in production")

    def __post_init__(self):
        # self._graph = preloaded_graph or nx.Graph()
        self._driver = GraphDatabase.driver("neo4j+s://91fbae6c.databases.neo4j.io", auth=("neo4j", "KWKPXfXcClDbUlmDdGgIQhU5mL1N4E_2CJp2BDFbEbw"))
        self._node_embed_algorithms = {
            "node2vec": self._node2vec_embed,
        }

    async def index_done_callback(self):
        print ("KG successfully indexed.")
    async def has_node(self, node_id: str) -> bool:
        entity_name_label = node_id.strip('\"')

        def _check_node_exists(tx, label):  
            query = f"MATCH (n:`{label}`) RETURN count(n) > 0 AS node_exists"  
            result = tx.run(query)  
            single_result = result.single()
            logger.info(
                    f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{single_result["node_exists"]}'
            )  
            
            return single_result["node_exists"]
        
        with self._driver.session() as session:  
            return session.read_transaction(_check_node_exists, entity_name_label)

        
    async def has_edge(self, source_node_id: str, target_node_id: str) -> bool:
        entity_name_label_source = source_node_id.strip('\"')
        entity_name_label_target = target_node_id.strip('\"')
       

        def _check_edge_existence(tx, label1, label2):  
            query = (  
                f"MATCH (a:`{label1}`)-[r]-(b:`{label2}`) "  
                "RETURN COUNT(r) > 0 AS edgeExists"  
            )  
            result = tx.run(query)  
            single_result = result.single()
            # if result.single() == None:
            #     print (f"this should not happen: ---- {label1}/{label2}   {query}")

            logger.info(
                    f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{single_result["edgeExists"]}'
            )  
            
            return single_result["edgeExists"]
        def close(self):  
            self._driver.close()   
        #hard code relaitionship type 
        with self._driver.session() as session:  
                result = session.read_transaction(_check_edge_existence, entity_name_label_source, entity_name_label_target)  
                return result   
        


    async def get_node(self, node_id: str) -> Union[dict, None]:
        entity_name_label = node_id.strip('\"')
        with self._driver.session() as session:  
            query = "MATCH (n:`{entity_name_label}`) RETURN n".format(entity_name_label=entity_name_label)
            result = session.run(query)
            for record in result:
                result = record["n"]
                logger.info(
                    f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{result}'
                )  
                return result
            


    async def node_degree(self, node_id: str) -> int:
        entity_name_label = node_id.strip('\"')


        def _find_node_degree(session, label):  
            with session.begin_transaction() as tx:  
                # query = "MATCH (n:`{label}`) RETURN n, size((n)--()) AS degree".format(label=label)
                query = f"""
                    MATCH (n:`{label}`)
                    RETURN COUNT{{ (n)--() }} AS totalEdgeCount
                """
                result = tx.run(query)  
                record = result.single()  
                if record:
                    edge_count = record["totalEdgeCount"]  
                    logger.info(
                        f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{edge_count}'
                    )  
                    return edge_count
                else:  
                    return None
                
        with self._driver.session()  as session:
            degree = _find_node_degree(session, entity_name_label)
            return degree


    # degree = session.read_transaction(get_edge_degree, 1, 2)
    async def edge_degree(self, src_id: str, tgt_id: str) -> int:
        entity_name__label_source = src_id.strip('\"')
        entity_name_label_target = tgt_id.strip('\"')
        with self._driver.session()  as session:
            query =  """MATCH (n1:`{node_label1}`)-[r]-(n2:`{node_label2}`)
                RETURN count(r) AS degree""".format(entity_name__label_source=entity_name__label_source, 
                                                    entity_name_label_target=entity_name_label_target)

            result = session.run(query)        
            record = result.single()
            logger.info(
                f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{record["degree"]}'
            )       
            return record["degree"]
    
    async def get_edge(self, source_node_id: str, target_node_id: str) -> Union[dict, None]:
        entity_name__label_source = source_node_id.strip('\"')
        entity_name_label_target = target_node_id.strip('\"')
        """
        Find all edges between nodes of two given labels
        
        Args:
            source_node_label (str): Label of the source nodes
            target_node_label (str): Label of the target nodes
            
        Returns:
            list: List of all relationships/edges found
        """
        with self._driver.session() as session:
            query = f"""
            MATCH (source:`{entity_name__label_source}`)-[r]-(target:`{entity_name_label_target}`)
            RETURN r
            """
            
            result = session.run(query)
            for logrecord in result:
                logger.info(
                    f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{logrecord["r"]}'
                )   


            return [record["r"] for record in result]
        


    async def get_node_edges(self, source_node_id: str):
        if self._graph.has_node(source_node_id):
            return list(self._graph.edges(source_node_id))
        return None

    async def get_node_edges(self, source_node_id: str):
        node_label = source_node_id.strip('\"')
          
        """
        Retrieves all edges (relationships) for a particular node identified by its label and ID.
        
        :param uri: Neo4j database URI
        :param username: Neo4j username
        :param password: Neo4j password
        :param node_label: Label of the node
        :param node_id: ID property of the node
        :return: List of dictionaries containing edge information
        """
        
        def fetch_edges(tx, label):
            query = f"""MATCH (n:`{label}`)
                OPTIONAL MATCH (n)-[r]-(connected)
                RETURN n, r, connected"""
            
            results = tx.run(query)

            edges = []
            for record in results:
                source_node = record['n']
                connected_node = record['connected']
                
                source_label = list(source_node.labels)[0] if source_node.labels else None
                target_label = list(connected_node.labels)[0] if connected_node and connected_node.labels else None
                
                if source_label and target_label:
                    print (f"appending: {[source_label, target_label]}")
                    edges.append([source_label, target_label])
            
            return edges

        with self._driver.session() as session:
            edges = session.read_transaction(fetch_edges,node_label)
            return edges


        # try:
        #     with self._driver.session() as session:
        #         if self.has_node(node_label):
        #             edges = session.read_transaction(fetch_edges,node_label)
        #             return list(edges)
        #     return edges
        # finally:
        #     print ("consider closign driver here")
        #     # driver.close()
    
    from typing import List, Tuple
    async def get_node_connections(driver: GraphDatabase.driver, label: str) -> List[Tuple[str, str]]:
        def run_query(tx):
            query = f"""
            MATCH (n:`{label}`)
            OPTIONAL MATCH (n)-[r]-(connected)
            RETURN n, r, connected
            """
            results = tx.run(query)
            
            connections = []
            for record in results:
                source_node = record['n']
                connected_node = record['connected']
                
                source_label = list(source_node.labels)[0] if source_node.labels else None
                target_label = list(connected_node.labels)[0] if connected_node and connected_node.labels else None
                
                if source_label and target_label:
                    connections.append((source_label, target_label))
            
            return connections

        with driver.session() as session:
            return session.read_transaction(run_query)

        



    #upsert_node
    async def upsert_node(self, node_id: str, node_data: dict[str, str]):
        label = node_id.strip('\"')
        properties = node_data
        """
        Upsert a node with the given label and properties within a transaction.
        If a node with the same label exists, it will:
        - Update existing properties with new values
        - Add new properties that don't exist
        If no node exists, creates a new node with all properties.
        
        Args:
            label: The node label to search for and apply
            properties: Dictionary of node properties
            
        Returns:
            Dictionary containing the node's properties after upsert, or None if operation fails
        """
        def _do_upsert(tx, label: str, properties: dict[str, Any]):

            """            
            Args:
                tx: Neo4j transaction object
                label: The node label to search for and apply
                properties: Dictionary of node properties
                
            Returns:
                Dictionary containing the node's properties after upsert, or None if operation fails
            """

            query = f"""
            MERGE (n:`{label}`)
            SET n += $properties
            RETURN n
            """
            # Execute the query with properties as parameters
            # with session.begin_transaction() as tx:  
            result = tx.run(query, properties=properties)
            record = result.single()
            if record:
                logger.info(
                    f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{dict(record["n"])}'
                )   
                return dict(record["n"])
            return None


        with self._driver.session() as session:
            with session.begin_transaction() as tx:
                try:
                    result = _do_upsert(tx,label,properties)
                    tx.commit()
                    return result
                except Exception as e:
                    raise  # roll back

               

    async def upsert_edge(self, source_node_id: str, target_node_id: str, edge_data: dict[str, str]) -> None:
        source_node_label = source_node_id.strip('\"')
        target_node_label = target_node_id.strip('\"')
        edge_properties = edge_data
        """
        Upsert an edge and its properties between two nodes identified by their labels.
        
        Args:
            source_node_label (str): Label of the source node (used as identifier)
            target_node_label (str): Label of the target node (used as identifier)
            edge_properties (dict): Dictionary of properties to set on the edge
        """
       

        
        def _do_upsert_edge(tx, source_node_label: str, target_node_label: str, edge_properties: dict[str, Any]) -> None:
            """
            Static method to perform the edge upsert within a transaction.
            
            The query will:
            1. Match the source and target nodes by their labels
            2. Merge the DIRECTED relationship
            3. Set all properties on the relationship, updating existing ones and adding new ones
            """
            # Convert edge properties to Cypher parameter string
            # props_string = ", ".join(f"r.{key} = ${key}" for key in edge_properties.keys())

            # """.format(props_string)
            query = f"""
            MATCH (source:`{source_node_label}`)
            WITH source
            MATCH (target:`{target_node_label}`)
            MERGE (source)-[r:DIRECTED]->(target)
            SET r += $properties
            RETURN r
            """

            result = tx.run(query, properties=edge_properties)
            logger.info(
                f'{inspect.currentframe().f_code.co_name}:query:{query}:result:{None}'
            )               
            return result.single()
            
        with self._driver.session() as session:
            session.execute_write(
                _do_upsert_edge,
                source_node_label,
                target_node_label,
                edge_properties
            )
            # return result

    async def _node2vec_embed(self):
        # async def _node2vec_embed(self):
        with self._driver.session()  as session:
            #Define the Cypher query
            options = self.global_config["node2vec_params"]
            logger.info(f"building embeddings with options {options}")
            query = f"""CALL gds.node2vec.write('91fbae6c', {
                options
                })
                YIELD nodeId, labels, embedding
                RETURN 
                nodeId AS id, 
                labels[0] AS distinctLabel, 
                embedding AS nodeToVecEmbedding
                """
            # Run the query and process the results
            results = session.run(query)
            embeddings = []
            node_labels = []
        for record in results:
            node_id = record["id"]
            embedding = record["nodeToVecEmbedding"]
            label = record["distinctLabel"]
            print(f"Node id/label: {label}/{node_id}, Embedding: {embedding}")
            embeddings.append(embedding)
            node_labels.append(label)
        return embeddings, node_labels

