/* This code sample provides a starter kit to implement server side logic for your Teams App in TypeScript,
 * refer to https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference for complete Azure Functions
 * developer guide.
 */

import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";

import data from "../data.json";

interface OrderedDish {
  name?: string;
  quantity?: number;
}
interface Order {
  dishes: OrderedDish[];
}

export async function placeOrder(
  req: HttpRequest,
  context: InvocationContext
): Promise<HttpResponseInit> {
  let order: Order | undefined;
  try {
    order = await req.json() as Order | undefined;
  }
  catch (error) {
    return {
      status: 400,
      jsonBody: { message: "Invalid JSON format" },
    } as HttpResponseInit;
  }

  if (!order.dishes || !Array.isArray(order.dishes)) {
    return {
      status: 400,
      jsonBody: { message: "Invalid order format" },
    } as HttpResponseInit;
  }

  let totalPrice = 0;
  const orderDetails = order.dishes.map(orderedDish => {
    const dish = data.find(d => d.name.toLowerCase().includes(orderedDish.name.toLowerCase()));
    if (dish) {
      totalPrice += dish.price * orderedDish.quantity;
      return {
        name: dish.name,
        quantity: orderedDish.quantity,
        price: dish.price,
      };
    }
    else {
      context.error(`Invalid dish: ${orderedDish.name}`);
      return null;
    }
  });

  if (orderDetails.includes(null)) {
    return {
      status: 400,
      jsonBody: { message: "One or more invalid dishes" },
    } as HttpResponseInit;
  }

  // Simulate order placement (e.g., saving to database)
  const orderId = Math.floor(Math.random() * 10000);

  return {
    status: 201,
    jsonBody: {
      order_id: orderId,
      status: "confirmed",
      total_price: totalPrice,
    },
  } as HttpResponseInit;
}

app.http("orders", {
  methods: ["POST"],
  authLevel: "anonymous",
  handler: placeOrder,
});
