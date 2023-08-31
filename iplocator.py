from flask import Flask, render_template, request
import requests
import socket
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'database.db'

def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    data = response.json()
    ip_address = data['ip']
    return ip_address

def get_location(ip_address):
    url = f"https://ipinfo.io/{ip_address}/json"
    response = requests.get(url)
    data = response.json()
    return data

def create_kml_file(name, description, latitude, longitude, filename):
    kml_template = """<?xml version="1.0" encoding="UTF-8"?>
    <kml xmlns="http://www.opengis.net/kml/2.2">
      <Placemark>
        <name>{name}</name>
        <description>{description}</description>
        <Point>
          <coordinates>{longitude},{latitude}</coordinates>
        </Point>
      </Placemark>
    </kml>
    """
    kml_content = kml_template.format(
        name=name,
        description=description,
        latitude=latitude,
        longitude=longitude
    )
    with open(filename, "w") as kml_file:
        kml_file.write(kml_content)

def init_db():
    with sqlite3.connect(DATABASE) as connection:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS searches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

@app.route("/", methods=['GET', 'POST'])
def index():
    init_db()  # Initialize the database
    
    if request.method == 'POST':
        user_ip = request.form['user_ip']
        try:
            socket.inet_aton(user_ip)  # Check if the input is a valid IP address
        except socket.error:
            error_message = "Invalid IP address format."
            return render_template("index.html", error_message=error_message)

        # Store the IP address in the database
        with sqlite3.connect(DATABASE) as connection:
            cursor = connection.cursor()
            cursor.execute("INSERT INTO searches (ip_address) VALUES (?)", (user_ip,))
        
        location_data = get_location(user_ip)  # Fetch location info
        if "error" in location_data:
            error_message = f"Error: {location_data['error']}"
            return render_template("index.html", error_message=error_message)
        
        # Rest of your code for creating KML file
        name = location_data.get("city")
        description = f"City: {location_data.get('city')}, Country: {location_data.get('country')}"
        latitude = location_data.get("loc").split(',')[0]
        longitude = location_data.get("loc").split(',')[1]
        create_kml_file(name, description, latitude, longitude, "location.kml")

        return render_template("index.html", location_info=location_data)

    return render_template("index.html")

if __name__ == "__main__":
    app.run()

