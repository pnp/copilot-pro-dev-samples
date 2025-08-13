import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

// Get CLI arguments
const command = process.argv[2];        // delete | update
const outputFilePath = process.argv[3]; // typescript file to write
const environment = process.argv[4];    // local|dev|[none]
const envVar = process.argv[5];         // environment variable in env file

// if delete...
if (command === 'delete') {
  if (fs.existsSync(outputFilePath)) {
    fs.unlinkSync(outputFilePath);
    console.log(`Deleted: ${outputFilePath}`);
  }
// else if append...
} else if (command === 'append') {
  // Load environment variables
  dotenv.config({ path: `./env/.env.${environment}` });

  // Ensure output directory exists
  fs.mkdirSync(path.dirname(outputFilePath), { recursive: true });

  // Get value from env
  const value = process.env[envVar];

  if (value === undefined) {
    throw new Error(`Environment variable ${envVar} is not defined in .env.${environment}`);
  }

  // Append to file
  const outputLine = `alias ${envVar} = "${value}";\n`;
  fs.appendFileSync(outputFilePath, outputLine);
  console.log(`Wrote: ${outputFilePath}`);
}