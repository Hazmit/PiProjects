from flask import Flask
from flask_restful import Api, Resource
from influxdb import InfluxDBClient

app = Flask(__name__)
api = Api(app)

client = InfluxDBClient(host='localhost', port=8086)
client.switch_database('solar_manager')

class GridOverride(Resource):
    def get(self, status, api_key):
        if(api_key == '15156a38-d7ce-4cca-b69d-3c7a6fd9b7e0'):
            if(status == 1):
                send_status = True
            else:
                send_status = False

            json_body = [
                    {
                        "measurement": "manager",
                        "tags": {
                         "control": "GridOverrideStatus"
                        },
                        "fields": {
                         "value": send_status
                        }
                    }
                ]

            client.write_points(json_body)

            return {"data": "success"}
        else:
            return {"data": "error, bad api key"}

api.add_resource(GridOverride, "/gridoverride/<int:status>/<string:api_key>")

if __name__ == "__main__":
    app.run(debug=True,host='192.168.1.41')
