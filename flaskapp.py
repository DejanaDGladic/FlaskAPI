from flask import Flask, request, jsonify
from databricks import sql
from dateutil import parser
import os

app = Flask(__name__)

# something like DTO
class BuildingDashboardDTO:
    def __init__(self, guid, id, number_of_meter_in_building, building_development_stage,
                 building_structure, tagged_date, initial_building_status, use_of_premises):
        self.guid = guid
        self.id = id
        self.number_of_meter_in_building = number_of_meter_in_building
        self.building_development_stage = building_development_stage
        self.building_structure = building_structure
        self.tagged_date = tagged_date
        self.initial_building_status = initial_building_status
        self.use_of_premises = use_of_premises

    def to_dict(self):
        return {
            'Guid': self.guid,
            'Id': self.id,
            'NumberOfMeterInBuilding': self.number_of_meter_in_building,
            'BuildingDevelopmentStage': self.building_development_stage,
            'BuildingStructure': self.building_structure,
            'TaggedDate': self.tagged_date.isoformat() if self.tagged_date else None,
            'InitialBuildingStatus': self.initial_building_status,
            'UseOfPremises': self.use_of_premises
        }
    
@app.route('/api/check', methods=['GET'])
def check():
    return jsonify("Checking...")

@app.route('/api/delta-data', methods=['GET'])
def get_delta_data():
    # get timestamp in ISO8601 format only
    start_ts = request.args.get('start_timestamp')
    end_ts = request.args.get('end_timestamp')

    # check ENV vars
    print(os.getenv('SERVER_HOSTNAME'))
    print(os.getenv('HTTP_PATH'))
    print(os.getenv('ACCESS_TOKEN'))

    try:
        start_dt = parser.isoparse(start_ts) if start_ts else None
        end_dt = parser.isoparse(end_ts) if end_ts else None
    except ValueError as ve:
        return jsonify({'error': f'Invalid timestamp format: {ve}'}), 400

    try:

        with sql.connect(
            server_hostname = os.getenv('SERVER_HOSTNAME'),
            http_path = os.getenv('HTTP_PATH'),
            access_token = os.getenv('ACCESS_TOKEN')
        ) as connection:
            cursor = connection.cursor()
            # for example between 2025-02-26T13:25:14.000 and 2025-03-03T13:43:35.000 - watch appropriate format ISO8601 (without +00:00)
            query = "SELECT * FROM `development`.`caims_common_gold_layer`.`building_dashboard` WHERE TaggedDate BETWEEN ? AND ?"
            query_params = []
            query_params.append(start_dt.isoformat())
            query_params.append(end_dt.isoformat())

            cursor.execute(query, query_params)
            rows = cursor.fetchall()
            dtos = [
                BuildingDashboardDTO(
                    guid=row['Guid'],
                    id=row['Id'],
                    number_of_meter_in_building=row['NumberOfMeterInBuilding'],
                    building_development_stage=row['BuildingDevelopmentStage'],
                    building_structure=row['BuildingStructure'],
                    tagged_date=row['TaggedDate'],
                    initial_building_status=row['InitialBuildingStatus'],
                    use_of_premises=row['UseOfPremises']
                ).to_dict() for row in rows]

            return jsonify(dtos)
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    # app.run(debug=True, host='0.0.0.0', port=8000)
    pass
