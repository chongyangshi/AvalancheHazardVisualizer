import sys
from pymongo import MongoClient, GEO2D

DB_SERVER = "mongodb://localhost:27017/"

class MongoDBManager:
    ''' A manager for the MongoDB used to store terrain data. 
        Note that MongoDB internally stores longitude before 
        latitude under all circumstances, so we convert it. '''
    
    def __init__(self, db_server=DB_SERVER):

        # Connect to server and test connection.
        try:
            self.__db_client = MongoClient(db_server, serverSelectionTimeoutMS=100)
            self.__db_client.server_info()
        except pymongo.errors.ServerSelectionTimeoutError as err:
            print("Error: Cannot connect to MongoDB Server, please check whether MongoDB Server is running.")
            raise
        
        # Assign databases.
        self.__aspects_db = self.__db_client['aspects']

        # Assign collections.
        self._aspects = self.__aspects_db['aspects']

        # Assign index items.
        self._aspects.create_index([("coordinate", GEO2D)])
    
    def add_aspect(self, latitude, longitude, aspect):
        ''' Add one aspect to aspects database.'''

        # Validate that all values to be floats.
        try:
            latitude = float(latitude)
            longitude = float(longitude)
            aspect = float(aspect)
        except ValueError:
            print("Error: add_aspect receives invalid record: " + str(latitude) + ", " + str(longitude) + ", " + str(aspect))
            return False

        # Drop invalid aspect.
        if (aspect < 0) or (aspect > 360):
            return False
        
        insertion_success = self._aspects.insert_one({
            "coordinate" : [longitude, latitude],
            "aspect": aspect
        })

        if insertion_success:
            return True
        else:
            return False
    
    def add_aspects(self, data):
        ''' Add aspects from data tuple (latitudes, longitudes, aspects) 
            into aspects database.'''

        # Validate that all values to be floats.
        records = []
        latitudes, longitudes, aspects = data
        if (len(latitudes) != len(longitudes)) or (len(longitudes) != len(aspects)):
            print("Error: add_aspects receives data of different lengths.")
            return False
        
        for i in range(len(latitudes)):
            try:
                latitude = float(latitudes[i])
                longitude = float(longitudes[i])
                asp = float(aspects[i])
                
                #Silently drop invalid data from the list, useful for terrain models with gaps, saving space.
                if (asp < 0) or (asp > 360):
                    continue
                else:
                    records.append({
                        "coordinate" : [longitude, latitude],
                        "aspect": asp
                    })
            except ValueError:
                print("Error: add_aspects receives invalid record: " + str(latitude) + ", " + str(longitude) + ", " + str(asp))
                return False
            
        # Insert records.
        insertion_success = self._aspects.insert_many(records)

        if insertion_success:
            return True
        else:
            return False

    def get_all_aspects(self):
        ''' Return all records. '''

        return self._aspects.find()
    
    def get_aspect(self, latitude, longitude, aspect):
        ''' Lookup one record with both latitude and longitude or aspect. 
            Key becomes match all if passed in as None.'''
        
        # Build the lookup object query.
        query = {}
        if (latitude is not None) and (longitude is not None):
            try:
                float(latitude)
                float(longitude)
                query["coordinate"] = [longitude, latitude]
            except ValueError:
                print("Error: get_aspect received an incorrect lookup coordinate set: " + str(latitude) + ", " + str(longitude))
                raise
                
        if aspect is not None:
            query["aspect"] = aspect

        # Perform DB lookup.
        result = self._aspects.find_one(query)

        return result
    
    def get_aspects_by_range(self, latitude_range, longitude_range):
        ''' Lookup records within an area, both ranges (inclusive) must be valid.'''
        
        # Build the lookup object query.
        try:
            if (latitude_range[1] > latitude_range[0]) and (longitude_range[1] > longitude_range[0]):
                lookup_box = [[longitude_range[0], latitude_range[0]], [longitude_range[1], latitude_range[1]]] 
            else:
                print("Error: get_aspects_by_range received an incorrectly ordered lookup range set: " + str(latitude_range) + " " + str(longitude_range))
                return False
        except:
            print("Error: get_aspects_by_range received an incorrect lookup range set: " + str(latitude_range) + " " + str(longitude_range))
            raise

        # Perform DB lookup.
        result = self._aspects.find({ "coordinate" : { "$within" : { "$box" : lookup_box }}})

        return result
    
    def get_nearest_aspect(self, latitude, longitude):
        ''' Lookup records within an area, both ranges (inclusive) must be valid.'''
        
        # Build the lookup object query.
        try:
            float(latitude)
            float(longitude)
            lookup_set = [longitude, latitude]
            
        except:
            print("Error: get_nearest_aspect received an incorrect lookup set: " + str(latitude) + ", " + str(longitude))
            raise

        # Perform DB lookup.
        result = self._aspects.find_one({ "coordinate" : { "$near" : lookup_set}})

        return result
    
    def remove_all_aspects(self):
        ''' Delete all aspects from database, caution! '''

        deletion_success = self._aspects.remove({})

        return deletion_success

    def remove_aspect(self, latitude, longitude):
        ''' Remove the aspect record at specified coordinate, exact match only.'''

        # Build deletion coordinate set.
        try:
            float(latitude)
            float(longitude)
            delete_set = [longitude, latitude]
        except ValueError:
            print("Error: remove_aspect received an incorrect deletion set: " + str(latitude) + ", " + str(longitude))
            raise
        
        # Execute deletion.
        deletion_success = self._aspects.remove({"coordinate": delete_set})

        return deletion_success
