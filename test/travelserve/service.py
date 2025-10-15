import base64
import os
import tempfile
from pathlib import Path

from pax import assign_rooms, format_results_json, load_passengers, load_rules

from bclib import edge

passenger_csv_path = Path(__file__).parent / "passengers.csv"
rules_path = Path(__file__).parent / "rules.json"

options = {
    "server": "localhost:8080",
    "router": "restful",
    "log_request": True
}


def assign_rooms_service(rules_file_path: str = str(rules_path), passenger_file_path: str = str(passenger_csv_path)):
    try:
        # Load passengers from file
        passengers = load_passengers(passenger_file_path)

        # Load rules from file
        rules = load_rules(rules_file_path)

        # Assign rooms
        results = assign_rooms(passengers, rules)

        # Format output
        output = format_results_json(results)

        return {
            "success": True,
            "total_rooms": len(output),
            "total_passengers": len(passengers),
            "passengers_source": str(passenger_csv_path),
            "assignments": output
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


app = edge.from_options(options)


@app.restful_action(app.post("assign-rooms"))
def assign_rooms_default(context: edge.RESTfulContext):
    edge.HttpHeaders.add_cors_headers(context)
    if not context.cms.files or len(context.cms.files) < 2:
        return {
            "success": False,
            "error": "Please upload both passengers CSV file and rules JSON file."
        }

    # Save uploaded passengers file temporarily
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv', encoding='utf-8') as temp_csv:
        passengers_content = context.cms.files[0].content.decode('utf-8')
        temp_csv.write(passengers_content)
        temp_csv_path = temp_csv.name

    # Save uploaded rules file temporarily
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_json:
        rules_content = context.cms.files[1].content.decode('utf-8')
        temp_json.write(rules_content)
        temp_json_path = temp_json.name

    results = assign_rooms_service(
        rules_file_path=temp_json_path, passenger_file_path=temp_csv_path)

    # Clean up temp file
    os.unlink(temp_json_path)
    os.unlink(temp_csv_path)

    return results


@app.restful_action(app.post("assign-rooms-with-rules"))
def assign_rooms_with_rules(context: edge.RESTfulContext):
    edge.HttpHeaders.add_cors_headers(context)
    # Save uploaded rules file temporarily
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json', encoding='utf-8') as temp_json:
        rules_content = base64.b64decode(
            context.cms.files[0].content_base64).decode('utf-8')
        temp_json.write(rules_content)
        temp_json_path = temp_json.name

    results = assign_rooms_service(rules_file_path=temp_json_path)

    # Clean up temp file
    os.unlink(temp_json_path)

    return results


@app.restful_action(app.get("assign-rooms-default"))
def assign_rooms_default(context: edge.RESTfulContext):
    edge.HttpHeaders.add_cors_headers(context)
    return assign_rooms_service()


app.listening()
