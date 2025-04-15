/* This code sample provides a starter kit to implement server side logic for your Teams App in TypeScript,
 * refer to https://docs.microsoft.com/en-us/azure/azure-functions/functions-reference for complete Azure Functions
 * developer guide.
 */

import { app, HttpRequest, HttpResponseInit, InvocationContext } from "@azure/functions";

import data from "../data.json";

export async function dishes(
  req: HttpRequest,
  context: InvocationContext
): Promise<HttpResponseInit> {
  const course = req.query.get('course');
  const allergensString = req.query.get('allergens');
  const allergens: string[] = allergensString ? allergensString.split(",") : [];
  const type = req.query.get('type');
  const name = req.query.get('name');

  // clone so that we're not modifying the original data
  let filteredDishes = [...data];

  if (name) {
    filteredDishes = filteredDishes.filter(dish => dish.name.toLowerCase().includes(name.toLowerCase()));
  }

  if (course) {
    filteredDishes = filteredDishes.filter(dish => dish.course === course);
  }

  if (type) {
    filteredDishes = filteredDishes.filter(dish => dish.type === type);
  }

  if (allergens.length > 0) {
    filteredDishes = filteredDishes.filter((dish) =>
      allergens.every(allergen => !dish.allergens.includes(allergen))
    );
  }

  return {
    status: 200,
    jsonBody: {
      dishes: filteredDishes
    },
  } as HttpResponseInit;
}

app.http("dishes", {
  methods: ["GET"],
  authLevel: "anonymous",
  handler: dishes,
});
