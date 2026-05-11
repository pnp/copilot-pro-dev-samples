import json
import logging
import random
from pathlib import Path

import azure.functions as func

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

DATA_FILE = Path(__file__).parent / "src" / "data.json"

try:
    _menu_data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
except Exception:
    logging.exception("Failed to load menu data")
    raise


@app.route(route="dishes", methods=["GET"])
def dishes(req: func.HttpRequest) -> func.HttpResponse:
    course = req.params.get("course")
    allergens_param = req.params.get("allergens")
    allergens = allergens_param.split(",") if allergens_param else []
    dish_type = req.params.get("type")
    name = req.params.get("name")

    filtered = list(_menu_data)

    if name:
        filtered = [d for d in filtered if name.lower() in d["name"].lower()]

    if course:
        filtered = [d for d in filtered if d["course"] == course]

    if dish_type:
        filtered = [d for d in filtered if d["type"] == dish_type]

    if allergens:
        filtered = [
            d for d in filtered
            if all(a not in d["allergens"] for a in allergens)
        ]

    return func.HttpResponse(
        json.dumps({"dishes": filtered}),
        status_code=200,
        mimetype="application/json",
    )


@app.route(route="orders", methods=["POST"])
def place_order(req: func.HttpRequest) -> func.HttpResponse:
    try:
        order = req.get_json()
    except ValueError:
        return func.HttpResponse(
            json.dumps({"message": "Invalid JSON format"}),
            status_code=400,
            mimetype="application/json",
        )

    if not order or not isinstance(order.get("dishes"), list):
        return func.HttpResponse(
            json.dumps({"message": "Invalid order format"}),
            status_code=400,
            mimetype="application/json",
        )

    total_price = 0.0
    order_details = []
    for ordered_dish in order["dishes"]:
        match = next(
            (d for d in _menu_data if d["name"].lower().find(ordered_dish["name"].lower()) >= 0),
            None,
        )
        if match:
            total_price += match["price"] * ordered_dish["quantity"]
            order_details.append({
                "name": match["name"],
                "quantity": ordered_dish["quantity"],
                "price": match["price"],
            })
        else:
            logging.error("Invalid dish: %s", ordered_dish.get("name"))
            return func.HttpResponse(
                json.dumps({"message": "One or more invalid dishes"}),
                status_code=400,
                mimetype="application/json",
            )

    order_id = random.randint(0, 9999)

    return func.HttpResponse(
        json.dumps({
            "order_id": order_id,
            "status": "confirmed",
            "total_price": total_price,
        }),
        status_code=201,
        mimetype="application/json",
    )