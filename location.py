from geopy.geocoders import Nominatim
import pandas as pd
import requests
from timezonefinder import TimezoneFinder
import pgeocode

zipcode_cache = {}


class weatherloc:

    def __init__(self, zipcode):
        self.zipcode = zipcode

        if zipcode in zipcode_cache:
            self.lat, self.lng, self.name = zipcode_cache[zipcode]
        else:
            # Call geocoding and timezone APIs
            self.lat, self.lng, self.name = self.find_location_by_zip()

        self.timezone = self.get_timezone()

        # Add to cache
        zipcode_cache[zipcode] = (self.lat, self.lng, self.name)



    def find_location_by_zip(self):
        """
        Find latitude and longitude using zipcode
        """
        if self.zipcode in zipcode_cache:
            return zipcode_cache[self.zipcode][0], zipcode_cache[self.zipcode][1]
        else:
            # Call geocoding API
            try:
                nomi = pgeocode.Nominatim('us')
                query = nomi.query_postal_code(self.zipcode)

                lat = query["latitude"]
                lng = query["longitude"]
                name = f"{query['place_name']}, {query['state_name']}"

                if lat:
                   # Cache for future
                   # zipcode_cache[self.zipcode] = (lat, lng, ...)
                    zipcode_cache[self.zipcode] = (lat, lng, name)
                    return lat, lng, name
                else:
                    print(f"Location not found for zip code: {self.zipcode}")
                    return None, None
            except Exception as e:
                print(f"Error: {e}")
                return None, None

    def get_timezone(self):
        # if self.zipcode in zipcode_cache:
        #     return zipcode_cache[self.zipcode][2]
        # else:
        tf = TimezoneFinder()
        timezone = tf.certain_timezone_at(lat=self.lat, lng=self.lng)
        return timezone

    def get_sunrise_sunset(self):
        """
        Find sunrise and sunset time using latitude and longitude
        """

        latitude, longitude = self.lat, self.lng

        api_url = f"https://api.sunrise-sunset.org/json?lat={latitude}&lng={longitude}&formatted=0"

        response = requests.get(api_url)

        data = response.json()

        # Extract sunrise and sunset times from the response
        sunrise = data["results"]["sunrise"]
        sunset = data["results"]["sunset"]

        sunrise = pd.to_datetime(sunrise)
        sunset = pd.to_datetime(sunset)

        return sunrise, sunset

