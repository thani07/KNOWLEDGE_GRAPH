# core/neo4j_client.py

from neo4j import GraphDatabase
from config import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD
from utils.logger import logger

class Neo4jClient:
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD),
                max_connection_lifetime=3600,
                max_connection_pool_size=50,
                connection_acquisition_timeout=60,
                connection_timeout=30,
            )
            # Test connection
            self.driver.verify_connectivity()
            logger.info("✅ Neo4j connection established successfully")
        except Exception as e:
            logger.error(f"❌ Neo4j connection failed: {e}")
            raise

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j driver closed")

    def run_read(self, query: str, params: dict = None):
        """
        Execute read query and return results.
        Handles result consumption inside transaction.
        """
        try:
            with self.driver.session() as session:
                result = session.execute_read(self._run_query, query, params or {})
                return result
        except Exception as e:
            logger.error(f"Neo4j read query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return []

    def run_write(self, query: str, params: dict = None):
        """
        Execute write query and return results.
        """
        try:
            with self.driver.session() as session:
                result = session.execute_write(self._run_query, query, params or {})
                return result
        except Exception as e:
            logger.error(f"Neo4j write query failed: {e}")
            logger.error(f"Query: {query}")
            logger.error(f"Params: {params}")
            return []

    @staticmethod
    def _run_query(tx, query: str, params: dict):
        """
        Internal query executor.
        Consumes all results before transaction closes.
        """
        result = tx.run(query, params)
        return [record.data() for record in result]

    def create_indexes(self):
        """
        Create full-text and property indexes for better search performance.
        """
        try:
            # Create full-text index on Entity name and description
            self.run_write("""
                CREATE FULLTEXT INDEX entity_search IF NOT EXISTS
                FOR (e:Entity)
                ON EACH [e.name, e.description, e.source_text]
            """)
            
            # Create property indexes
            self.run_write("""
                CREATE INDEX entity_name IF NOT EXISTS
                FOR (e:Entity) ON (e.name)
            """)
            
            self.run_write("""
                CREATE INDEX entity_type IF NOT EXISTS
                FOR (e:Entity) ON (e.type)
            """)
            
            self.run_write("""
                CREATE INDEX entity_uid IF NOT EXISTS
                FOR (e:Entity) ON (e.uid)
            """)
            
            self.run_write("""
                CREATE INDEX document_pdf_id IF NOT EXISTS
                FOR (d:Document) ON (d.pdf_id)
            """)
            
            logger.info("✅ Neo4j indexes created successfully")
        except Exception as e:
            logger.warning(f"Index creation warning (may already exist): {e}")


# Global instance
neo4j_client = Neo4jClient()

# Create indexes on startup
try:
    neo4j_client.create_indexes()
except Exception as e:
    logger.warning(f"Could not create indexes: {e}")
