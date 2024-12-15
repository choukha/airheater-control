import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import logging
from pathlib import Path

class DatabaseHandler:
    def __init__(self, db_path="airheater.db"):
        """Initialize database connection and create tables if they don't exist"""
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database with schema"""
        try:
            # Create database directory if it doesn't exist
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Initialize database
            with sqlite3.connect(self.db_path) as conn:
                # Read and execute schema
                schema_path = Path(__file__).parent / "database_schema.sql"
                with open(schema_path) as f:
                    conn.executescript(f.read())
                    
            logging.info(f"Database initialized at {self.db_path}")
            
        except Exception as e:
            logging.error(f"Database initialization error: {e}")
            raise
            
    def store_measurement(self, temperature, filtered_temp, control_signal, 
                         setpoint, kp, ti):
        """Store a measurement in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO measurements 
                    (temperature, temperature_filtered, control_signal, 
                     setpoint, kp, ti)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (temperature, filtered_temp, control_signal, 
                      setpoint, kp, ti))
                
        except sqlite3.Error as e:
            logging.error(f"Error storing measurement: {e}")
            
    def get_recent_data(self, minutes=10):
        """Get data from last X minutes."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT timestamp, temperature, temperature_filtered, control_signal, setpoint
                    FROM measurements
                    WHERE timestamp >= datetime('now', '-' || ? || ' minutes')
                    ORDER BY timestamp ASC
                '''
                df = pd.read_sql_query(query, conn, params=(minutes,))
                if not df.empty:
                    df['timestamp'] = pd.to_datetime(df['timestamp'])  # Ensure datetime format
                return df
        except sqlite3.Error as e:
            logging.error(f"Error retrieving recent data: {e}")
            return pd.DataFrame()

            
    def get_latest_values(self):
        """Get most recent measurement"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                query = '''
                    SELECT * FROM measurements 
                    ORDER BY timestamp DESC 
                    LIMIT 1
                '''
                return pd.read_sql_query(query, conn)
                
        except sqlite3.Error as e:
            logging.error(f"Error retrieving latest values: {e}")
            return pd.DataFrame()
            
    def clear_historical_data(self):
        """Clear all measurements from database"""
        success = False
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get count before deletion
            cursor.execute("SELECT COUNT(*) FROM measurements")
            count_before = cursor.fetchone()[0]
            
            # Delete all records
            cursor.execute("DELETE FROM measurements")
            conn.commit()
            
            # Verify deletion
            cursor.execute("SELECT COUNT(*) FROM measurements")
            count_after = cursor.fetchone()[0]
            
            # Vacuum to reclaim space
            conn.execute("VACUUM")
            conn.commit()
            
            success = (count_after == 0 and count_before > 0)
            logging.info(f"Cleared {count_before} records from database")
            
        except sqlite3.Error as e:
            logging.error(f"Error clearing data: {e}")
            success = False
        finally:
            if conn:
                conn.close()
            
        return success
            
    def export_to_csv(self, filepath=None):
        """Export database to CSV"""
        if filepath is None:
            filepath = f"airheater_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
        try:
            with sqlite3.connect(self.db_path) as conn:
                df = pd.read_sql_query("SELECT * FROM measurements", conn)
                df.to_csv(filepath, index=False)
                return True
                
        except Exception as e:
            logging.error(f"Error exporting data: {e}")
            return False
            
    def get_statistics(self):
        """Get basic statistics from the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                stats = {}
                
                # Get total records and time range
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_records,
                        MIN(timestamp) as first_record,
                        MAX(timestamp) as last_record,
                        AVG(temperature) as avg_temp,
                        MIN(temperature) as min_temp,
                        MAX(temperature) as max_temp,
                        AVG(control_signal) as avg_control
                    FROM measurements
                ''')
                
                (stats['total_records'], stats['first_record'], 
                 stats['last_record'], stats['avg_temperature'],
                 stats['min_temperature'], stats['max_temperature'],
                 stats['avg_control_signal']) = cursor.fetchone()
                
                return stats
                
        except sqlite3.Error as e:
            logging.error(f"Error getting statistics: {e}")
            return None

    def cleanup_old_data(self, days=30):
        """Remove data older than specified days"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    DELETE FROM measurements 
                    WHERE timestamp < datetime('now', '-' || ? || ' days')
                ''', (days,))
                return True
                
        except sqlite3.Error as e:
            logging.error(f"Error cleaning up old data: {e}")
            return False